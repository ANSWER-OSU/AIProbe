using System;
using System.Diagnostics;
using System.Text;
using System.Xml.Serialization;
using AIprobe.EnvironmentGenerator;
using AIprobe.Logging;
using AIprobe.Models;
using AIprobe.Parsers;
using AIprobe.TaskGenerator;
using AIprobe.InstructionGenerator;
using AIprobe.Preprocessing;
using Action = System.Action;
using Environment = AIprobe.Models.Environment;
using System.Threading.Tasks;
using System.Collections.Concurrent;

namespace AIprobe
{
    internal class Aiprobe
    {
        public static string envConfigFile = String.Empty;
        public static string pythonScriptFilePath = String.Empty;
        public static string pythonInterpreterPath = String.Empty;
        public static string resultFolder = String.Empty;
        public static string tempFolder = String.Empty;
        public static string testingHardCoddedEnvs = String.Empty;
        public static double totalEnviroementState = 0;
        public static Dictionary<double, double> unsafeStatePosition = new Dictionary<double, double>();
        public static int seed = 0;
        private static int taskGenrationTime = 0;
        private static double processingTime = 0;
        private static int instructionGenerationTime = 0;
        private static ActionSpace actionSpace = new ActionSpace();


        static async Task Main(string[] args)
        {
            #region EnviromentVariable

            string aiprobe_root_path = System.Environment.GetEnvironmentVariable("AIPROBE_HOME");
            string py_path = System.Environment.GetEnvironmentVariable("PYTHON_HOME");
            
            Console.WriteLine($"aiprobe_root_path: {aiprobe_root_path}");
            Console.WriteLine($"py_path: {py_path}");

            // Get Aiprobe config path  
            if (aiprobe_root_path == null)
            {
                //aiprobe_root_path = "/Users/rahil/Documents/GitHub/AIProbe/csharp";
                Console.WriteLine(
                    "Error! please set AIPROBE_HOME env variable to point to \"<path-to>AIProbe/csharp\" directory.");
                return;
            }

            // Get the python pathSystem
            if (py_path == null)
            {
                //py_path = "/opt/anaconda3/envs/aiprobe/bin/python";
                Console.WriteLine("Error! please set PYTHON_HOME env variable to point to \"<path-to-aiprobe conda env>/bin/python\" file.");
                return;
            }

            #endregion

            Console.WriteLine("Reading the config file and Setting environment variables...");
            SetStaticVariable(aiprobe_root_path, py_path);

            ConcurrentQueue<Environment> envireomentQueue = getEnviromentQueue();

            CancellationTokenSource cts = new CancellationTokenSource();
            cts.CancelAfter(TimeSpan.FromSeconds(processingTime)); 

            EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator();
            int instructionFound = 0;
            int totalTasks = 0;
            try
            {
                //envireomentQueue.TryDequeue(out Environment env);
                
                //var tasks = envTaskGenerator.GenerateTasksUsingOrthogonalSampling(env, 20, seed: 42, outputFilePath: "generated_orthogonal_samples.csv");

                var envTaskqueue = await GetEnvironmentTaskQueueAsync(envireomentQueue, resultFolder);
                // Queue<(string initialPath, string finalPath)> envTaskqueue = 
                //     await GetTasksUsingOrthogonalSamplingAsync(envireomentQueue, resultFolder);
                //
                //
                totalTasks = envTaskqueue.Count;
                InstructionChecker instructionChecker = new InstructionChecker();
                while (envTaskqueue.Count > 0)
                {
                    cts.Token.ThrowIfCancellationRequested(); // Check for cancellation
                    Stopwatch stopwatch = Stopwatch.StartNew();
                    // Dequeue an item
                    var (initialPath, finalPath) = envTaskqueue.Dequeue();

                    if (File.Exists(initialPath) && File.Exists(finalPath))
                    {
                        Console.WriteLine($"{initialPath}\n{finalPath}");
                        // Get the directory of the file
                        string directoryPath = Path.GetDirectoryName(initialPath);

                        // Split the directory path into parts
                        string[] pathParts = directoryPath.Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);

                        // Get the last two parts
                        string lastTwoDirectories = string.Join(Path.DirectorySeparatorChar.ToString(), pathParts[^3..^0]);
                        
                        string state = Path.Combine(directoryPath, $"AIprobe.json");

                        Console.WriteLine($"Environment: {lastTwoDirectories}");
                    
                        EnvironmentParser initialParser = new EnvironmentParser(initialPath);
                        Environment initialEnvironment = initialParser.ParseEnvironment();

                        EnvironmentParser finalParser = new EnvironmentParser(finalPath);
                        Environment finalEnvironment = finalParser.ParseEnvironment();

                        string finalEnvironmentHash = HashGenerator.ComputeEnvironmentHash(finalEnvironment);
                        string initialEnvHash = HashGenerator.ComputeEnvironmentHash(initialEnvironment);

                        List<object[]> taskResults = instructionChecker.InstructionExists(initialEnvironment,actionSpace,instructionGenerationTime , initialEnvHash, finalEnvironmentHash, out bool instructionExists);
                        if (instructionExists)
                        {
                            instructionFound++;
                        }
                        Logger.LogInfo($"Total {unsafeStatePosition.Keys.Count()} unsafe states found in the {lastTwoDirectories}");
                        string unsafeStateDataPath = Path.Combine(Path.GetDirectoryName(initialPath), $"unsafeState.json");
                        ResultSaver.SaveDictionaryToJson(unsafeStatePosition, unsafeStateDataPath);
                        Logger.LogInfo($"Unsafe states data stored at {unsafeStateDataPath}");
                        ResultSaver.SaveTaskResults(taskResults, state);
                        stopwatch.Stop();

                        // Log execution time
                        Logger.LogInfo($"Task execution time: {stopwatch.Elapsed.TotalMilliseconds/100} s");
                    }
                    else
                    { 
                        LogAndDisplay($"One or both files are missing for the task.");
                    }
                }
            }
            catch (OperationCanceledException)
            {
                LogAndDisplay($"Total tasks: {totalTasks}");
                LogAndDisplay($"Total Instruction found : {instructionFound}");
                LogAndDisplay("The operation was canceled due to a timeout.");
            }
            finally
            {
                LogAndDisplay($"Total tasks: {totalTasks}");
                LogAndDisplay($"Total Instruction found : {instructionFound}");
                cts.Dispose();
            }
        }


        static void Mainsd(string[] args)
        {
            // get the root path
            string aiprobe_root_path = System.Environment.GetEnvironmentVariable("AIPROBE_HOME");


            if (aiprobe_root_path == null)
            {
                //aiprobe_root_path = "/Users/rahil/Documents/GitHub/AIProbe/csharp";

                Console.WriteLine(
                    "Error! please set AIPROBE_HOME env variable to point to \"<path-to>AIProbe/csharp\" directory.");
            }

            // get the python pathSystem
            string py_path = System.Environment.GetEnvironmentVariable("PYTHON_HOME");
            if (py_path == null)
            {
                //py_path = "/opt/anaconda3/envs/aiprobe/bin/python";
                Console.WriteLine(
                    "Error! please set PYTHON_HOME env variable to point to \"<path-to-aiprobe conda env>/bin/python\" file.");
            }


            // Parse the AIprobe configuration file
            ConfigParser configParser = new ConfigParser();
            AIprobeConfig config = configParser.ParseConfig();
            if (config == null)
            {
                Logger.LogError("Failed to parse Aiprobe's configuration file. Exiting...");
                return;
            }

            // Set the log file path
            string logFilePath = aiprobe_root_path + "/" + config.LogSettings.LogFilePath;
            //string logFilePath = "/tmp/aiprobe_log.txt";

            
            Logger.Initialize(logFilePath);

            Logger.LogInfo("Starting AIprobe...");
            pythonScriptFilePath = aiprobe_root_path + "/../" + config.PythonSettings.ScriptFilePath;
            pythonInterpreterPath = py_path; //config.PythonSettings.PythonEnvironment;
            resultFolder = aiprobe_root_path + "/" + config.ResultSetting.ResultFolderPath;


            Console.WriteLine($"Result folder at: {resultFolder}");
            Logger.LogInfo($"Result folder at: {resultFolder}");
            envConfigFile = aiprobe_root_path + "/" + config.FileSettings.InitialEnvironmentFilePath;
            Logger.LogInfo($"Initial environment File Path: {config.FileSettings.InitialEnvironmentFilePath}");
            Console.WriteLine($"Initial environment file path: {envConfigFile}");

            // Parse the initial environment file
            EnvironmentParser intialParser = new EnvironmentParser(envConfigFile);
            Environment initialEnvironment = intialParser.ParseEnvironment();

            //AttributePreprocessor attributePreprocessor = new AttributePreprocessor();
            //attributePreprocessor.ProcessAttributes(initialEnvironment);

            if (initialEnvironment == null)
            {
                Console.WriteLine("Error parsing environment. Please check the input file.");
                Logger.LogError("Error parsing environment. Please check the input file.");
                return;
            }


            int seed = config.RandomSettings.Seed;

            ConcurrentQueue<Environment> environmentQueue =
                EnvConfigGenerator.GenerateEnvConfigsQueue(initialEnvironment, seed);


            //List<Environment> environmentsList = EnvConfigGenerator.GenerateEnvConfigs(initialEnvironment, seed);
            //Console.WriteLine($"Enviroment list size: {environmentsList.Count}");


            //EnvironmentExporter.SaveEnvironmentsToCsv(environmentsList, "/Users/rahil/Documents/GitHub/AIProbe/csharp/results/Result_LavaEnv_6161/sampled_values.csv");


            // List<Environment> reduceList =  OrthogonalSampler.ReduceSampleSize(environmentsList,10);
            //
            // EnvironmentExporter.SaveEnvironmentsToCsv(reduceList, "/Users/rahil/Documents/GitHub/AIProbe/csharp/results/Result_LavaEnv_6161/reduces_sampled_values.csv");


            long envCounter = 1;


            // var task = Task.Run(() => ProcessEnvironments(environmentsList,seed,envCounter));
            //  task.Wait(); // Block until the task completes
            //  

            //  // Start from 1 for environment numbering
            //   var envCounterLock = new object();
            //
            //   var parallelOptions = new ParallelOptions
            //   {
            //       MaxDegreeOfParallelism = System.Environment.ProcessorCount // Use all logical processors
            //   };
            //   
            // ConcurrentDictionary<Environment, List<Environment>> envTaskMapping = new();
            //
            // Parallel.ForEach(environmentsList, parallelOptions, env =>
            // {
            //     double currentEnvNumber;
            //
            //     // Safely increment the environment counter
            //     lock (envCounterLock)
            //     {
            //         currentEnvNumber = envCounter++;
            //     }
            //
            //     // Generate the directory path for the environment
            //     string environmentDirPath = $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/{currentEnvNumber}";
            //
            //     // Ensure the directory exists
            //     Directory.CreateDirectory(environmentDirPath);
            //
            //     // Generate the environment file path
            //     string environmentFilePath = $"{environmentDirPath}/config.xml";
            //
            //     // Write the environment configuration
            //     WriteEnvironment(env, environmentFilePath);
            //
            //     // Generate tasks for the environment
            //     var taskCounter = 1; // Local task counter for this environment
            //     var taskCounterLock = new object();
            //     List<Environment> tasks = EnvTaskGenerator.TaskGenerator(env, seed);
            //
            //     envTaskMapping[env] = tasks;
            //     // Parallel.ForEach(tasks, parallelOptions, task =>
            //     // {
            //     //     int currentTaskNumber;
            //     //
            //     //     // Safely increment the task counter
            //     //     lock (taskCounterLock)
            //     //     {
            //     //         currentTaskNumber = taskCounter++;
            //     //     }
            //     //
            //     //     // Generate the task file path
            //     //     string taskFilePath = $"{environmentDirPath}/task{currentTaskNumber}.xml";
            //     //
            //     //     // Ensure the directory exists (optional, redundant if done for the environment directory)
            //     //     Directory.CreateDirectory(environmentDirPath);
            //     //
            //     //     // Write the task configuration
            //     //     WriteEnvironment(task, taskFilePath);
            //     // }); 
            //     
            //     
            // });
            //
            // Console.Write(envTaskMapping.Count);

            double EnvCount = 0;


            Queue<(Environment Env, List<Environment> Tasks)> environmentTaskQueue =
                new Queue<(Environment, List<Environment>)>();

            Stopwatch overallStopwatch = Stopwatch.StartNew(); // Start the stopwatch for total processing time
            int processedEnvironments = 0; // Track processed environments
            int totalTasks = 0; // Track total tasks
            int totalEnvironments = environmentQueue.Count; // Total number of environments
            int envCount = 0; // Counter for environments


            // Start from the current cursor position
            int cursorTop = Console.CursorTop;
            Stopwatch progressStopwatch = Stopwatch.StartNew(); // Measure time since the last progress update
            int updateIntervalInSeconds = 10;
            bool firstUpdate = true;
            // while (environmentQueue.Count > 0)
            // {
            //     Stopwatch envStopwatch = Stopwatch.StartNew(); // Measure time for the current environment
            //
            //     // Dequeue the next environment
            //     var envBool = environmentQueue.TryDequeue(out var env);
            //     envCount++;
            //
            //     // Prepare environment directory
            //     
            //
            //     // Measure task generation time
            //     Stopwatch taskGeneratorStopwatch = Stopwatch.StartNew();
            //     List<Environment> tasks = EnvTaskGenerator.TaskGenerator(env, seed);
            //     taskGeneratorStopwatch.Stop();
            //     double taskGenerationTime = taskGeneratorStopwatch.Elapsed.TotalSeconds;
            //
            //     // Enqueue the environment and its tasks
            //     environmentTaskQueue.Enqueue((env, tasks));
            //
            //     envStopwatch.Stop(); // Stop the environment stopwatch
            //     double environmentTime = envStopwatch.Elapsed.TotalSeconds;
            //
            //     // Increment processed environments
            //     processedEnvironments++;
            //
            //     // Calculate metrics
            //     double elapsedTime = overallStopwatch.Elapsed.TotalSeconds;
            //     double averageTimePerEnvironment = elapsedTime / processedEnvironments;
            //     double estimatedTimeRemaining = averageTimePerEnvironment * (totalEnvironments - processedEnvironments);
            //
            //
            //     if (firstUpdate || progressStopwatch.Elapsed.TotalSeconds >= updateIntervalInSeconds)
            //     {
            //         // Reset the progress stopwatch
            //         progressStopwatch.Restart();
            //
            //         firstUpdate = false;
            //
            //         // Update console output
            //         Console.SetCursorPosition(0, cursorTop); // Reset the cursor to the start of the block
            //         Console.WriteLine($"Environment {envCount} processing took {environmentTime:F2} seconds.");
            //         Console.WriteLine($"Processed: {processedEnvironments}/{totalEnvironments} environments");
            //         Console.WriteLine($"Elapsed Time: {elapsedTime:F2} seconds");
            //         Console.WriteLine($"Average Time per Environment: {averageTimePerEnvironment:F2} seconds");
            //         Console.WriteLine($"Estimated Time Remaining: {estimatedTimeRemaining:F2} seconds");
            //     }
            // }


            // foreach (var env in environmentsList)
            // {
            //    
            //     
            //     Stopwatch envStopwatch = Stopwatch.StartNew(); // Measure time for the current environment
            //
            //     EnvCount += 1;
            //     
            //     string environmentDirPath = $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/{EnvCount}";
            //     if (!Directory.Exists(environmentDirPath))
            //     {
            //         Directory.CreateDirectory(environmentDirPath); // Create the directory if it doesn't exist
            //     }
            //
            //     
            //     string environmentFilePath = $"{environmentDirPath}/config.xml";
            //     // string environmentFilePath =
            //     //     $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/{EnvCount}/config.xml";
            //     //WriteEnvironment(env, environmentFilePath);
            //     
            //     
            //     
            //     // Measure task generation time
            //     Stopwatch taskGeneratorStopwatch = Stopwatch.StartNew();
            //     List<Environment> tasks = EnvTaskGenerator.TaskGenerator(env, seed);
            //     taskGeneratorStopwatch.Stop();
            //     double taskGenerationTime = taskGeneratorStopwatch.Elapsed.TotalSeconds;
            //
            //     Console.WriteLine($"Environment {EnvCount} task generation took {taskGenerationTime:F2} seconds.");
            //
            //     environmentTaskQueue.Enqueue((env, tasks));
            //     
            //     // Process tasks in parallel
            //     var parallelOptions = new ParallelOptions
            //     {
            //         MaxDegreeOfParallelism = System.Environment.ProcessorCount
            //     };
            //
            //     int taskCounter = 1;
            //     var taskCounterLock = new object();
            //
            //     // Parallel.ForEach(tasks, parallelOptions, task =>
            //     // {
            //     //     int currentTaskNumber;
            //     //     lock (taskCounterLock)
            //     //     {
            //     //         currentTaskNumber = taskCounter++;
            //     //     }
            //     //
            //     //     string taskPath =
            //     //         $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/{EnvCount}/task{currentTaskNumber}.xml";
            //     //     WriteEnvironmentAsync(task, taskPath);
            //     // });
            //     //
            //     // // Update total tasks
            //     // lock (taskCounterLock)
            //     // {
            //     //     totalTasks += tasks.Count;
            //     // }
            //
            //     envStopwatch.Stop(); // Stop the environment stopwatch
            //     double environmentTime = envStopwatch.Elapsed.TotalSeconds;
            //
            //     // Increment the processed environments counter
            //     processedEnvironments++;
            //
            //     // Calculate metrics
            //     double elapsedTime = overallStopwatch.Elapsed.TotalSeconds;
            //     double averageTimePerEnvironment = elapsedTime / processedEnvironments;
            //     double estimatedTimeRemaining = averageTimePerEnvironment * (totalEnvironments - processedEnvironments);
            //
            //     // Log metrics for the current environment
            //     Console.WriteLine($"Environment {EnvCount} processing took {environmentTime:F2} seconds.");
            //     Console.WriteLine($"Processed: {processedEnvironments}/{totalEnvironments} environments");
            //     Console.WriteLine($"Elapsed Time: {elapsedTime:F2} seconds");
            //     Console.WriteLine($"Average Time per Environment: {averageTimePerEnvironment:F2} seconds");
            //     Console.WriteLine($"Estimated Time Remaining: {estimatedTimeRemaining:F2} seconds");
            // }


            Logger.LogInfo("Initial Environment parsed successfully.");

            // Parse the action space of the Environment.
            Logger.LogInfo(
                $"Action Space File Path: {aiprobe_root_path + "/" + config.FileSettings.ActionSpaceFilePath}");
            ActionSpaceParser actionSpaceParser =
                new ActionSpaceParser(aiprobe_root_path + "/" + config.FileSettings.ActionSpaceFilePath);
            ActionSpace actionSpace = actionSpaceParser.ParseActionSpace();
            testingHardCoddedEnvs = aiprobe_root_path + "/" + "Data/13_lava_env";


            //EnvConfigGenerator envConfigGenerator = new EnvConfigGenerator();
            //EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator(config.RandomSettings.Seed);
            //EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator();
            Logger.LogInfo($"Running for seed no {config.RandomSettings.Seed} ");
            InstructionChecker instructionChecker = new InstructionChecker();

            // generating new env from inital env 
            //Logger.LogInfo($"Enviroment generation Started");
            //List<AIprobe.Models.Environment> environments = envConfigGenerator.GenerateEnvConfigs(initialEnvironment, config.RandomSettings.Seed);
            //Logger.LogInfo($"Enviroment generation completed. {environments.Count} environment were generated.");
            //var env = initialEnvironment;

            int count = 1;
            //foreach(AIprobe.Models.Environment env in environments)
            //{
            //string resultEnviromentDir = resultFolder;
            //string resultEnviromentPath = Path.Combine(resultFolder, $"Env_{count}");
            //Directory.CreateDirectory(Path.GetDirectoryName(resultEnviromentPath));
            // Generating new tasks list
            Logger.LogInfo($"Creating new tasks for Environment {count}");
            // List<(AIprobe.Models.Environment, Environment)> tasksList =
            //     envTaskGenerator.GenerateTasks(initialEnvironment, config.TimeSettings.TaskGenerationTime);
            DateTime startTime = DateTime.Now;


            envCount = 1;
            int tasksCount = 1;
            int totaltaskachieved = 0;

            while (environmentTaskQueue.Count > 0)
            {
                var currentEnviroment = environmentTaskQueue.Dequeue();

                Environment initialEnv = currentEnviroment.Env;
                string initialEnvironmentHash = HashGenerator.ComputeEnvironmentHash(initialEnv);


                string environmentDirPath = $"{resultFolder}/Env_{envCount}";
                if (!Directory.Exists(environmentDirPath))
                {
                    Directory.CreateDirectory(environmentDirPath); // Create the directory if it doesn't exist
                }


                tasksCount = 0;

                foreach (var task in currentEnviroment.Tasks)
                {
                    string finalEnvironmentHash = HashGenerator.ComputeEnvironmentHash(task);

                    Console.WriteLine($"{initialEnvironmentHash} : {finalEnvironmentHash}");


                    string folderPath = $"{environmentDirPath}/Task_{tasksCount}";
                    if (!Directory.Exists(folderPath))
                    {
                        Directory.CreateDirectory(folderPath); // Create the directory if it doesn't exist
                    }


                    string environmentFilePath = $"{folderPath}/initialState.xml";

                    WriteEnvironment(initialEnv, environmentFilePath);


                    string taskFilePath = $"{folderPath}//finalState.xml";
                    WriteEnvironment(task, taskFilePath);


                    tasksCount++;
                    //Console.WriteLine($"{initialEnvironmentHash} : {finalEnvironmentHash}");
                    List<object[]> taskResults = instructionChecker.InstructionExists(initialEnv, actionSpace,
                        config.TimeSettings.InstructionGenerationTime, initialEnvironmentHash, finalEnvironmentHash,
                        out bool instructionExists);
                }


                envCount++;
            }
            // foreach (var task in tasksList)
            // {
            //     
            //     
            //     string taskFolder = Path.Combine(resultFolder, $"Task_{tasksCount}");
            //     string initalStateTaskPath = Path.Combine(taskFolder, "initialState.xml");
            //     string finalStateTaskPath = Path.Combine(taskFolder, "finalState.xml");
            //     string instructionsPath = Path.Combine(taskFolder, "AIprobe.json");
            //     tempFolder = Path.Combine(taskFolder, $"Temp_{tasksCount}");
            //     Directory.CreateDirectory(tempFolder);
            //     Directory.CreateDirectory(Path.GetDirectoryName(initalStateTaskPath));
            //     Directory.CreateDirectory(Path.GetDirectoryName(tempFolder));
            //
            //     File.Create(initalStateTaskPath).Dispose();
            //     File.Create(finalStateTaskPath).Dispose();
            //
            //     EnvironmentParser initalStateTaskPasser = new EnvironmentParser(initalStateTaskPath);
            //     initalStateTaskPasser.WriteEnvironment(task.Item1, out string intialStateHashValue);
            //      //
            //     EnvironmentParser finalStateTaskPasser = new EnvironmentParser(finalStateTaskPath);
            //     finalStateTaskPasser.WriteEnvironment(task.Item2, out string finalStateHashValue);
            //
            //
            //     // EnvironmentParser initalxml = new EnvironmentParser("/Users/rahil/Downloads/Archive/Task_10/initialState.xml");
            //     // AIprobe.Models.Environment initialEnvironmentxml = initalxml.ParseEnvironment();
            //     // // //
            //     // EnvironmentParser finalxml = new EnvironmentParser("/Users/rahil/Downloads/Archive/Task_10/finalState.xml");
            //     // AIprobe.Models.Environment finaEnvironmentxml = finalxml.ParseEnvironment();
            //     // //
            //     // initalxml.WriteEnvironment(initialEnvironmentxml,out string intialStateHashValue);
            //     // //
            //     // //
            //     // finalxml.WriteEnvironment(finaEnvironmentxml,out string finalStateHashValue);
            //     //
            //     // List<object[]> taskResults = instructionChecker.InstructionExists(initialEnvironmentxml, finaEnvironmentxml, actionSpace,
            //     //     config.TimeSettings.InstructionGenerationTime, intialStateHashValue, finalStateHashValue,
            //     //     out bool instructionExists);
            //     //
            //     //
            //     //
            //
            //     List<object[]> taskResults = instructionChecker.InstructionExists(task.Item1, task.Item2, actionSpace,
            //         config.TimeSettings.InstructionGenerationTime, intialStateHashValue, finalStateHashValue,
            //         out bool instructionExists);
            //     ResultSaver.SaveTaskResults(taskResults, instructionsPath);
            //     if (instructionExists)
            //     {
            //         totaltaskachieved++;
            //         Logger.LogInfo($"Task {tasksCount} instructions found saved to {taskFolder}");
            //     }
            //     Logger.LogInfo($"Total no of state explored: {totalEnviroementState}");
            //
            //     tasksCount++;
            //
            //
            //     Logger.LogInfo($"Total task achieved {totaltaskachieved} from {tasksList.Count} task.");
            //     
            //     string unsafeStateData  = Path.Combine(resultFolder, $"unsafeSate.json");
            //     ResultSaver.SaveDictionaryToJson(unsafeStatePosition, unsafeStateData);
            //     Logger.LogInfo($" Unsafe states data stored at {unsafeStateData}");
            //
            //
            //     // List<object[]> taskResults = instructionChecker.InstructionExists(initialEnvironment,tasksList[0],actionSpace,config.TimeSettings.InstructionGenerationTime,initalEnviromentHashValue);
            //     //
            //     // ResultSaver.SaveTaskResults(taskResults,"/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/AIprobe.json");
            //     //
            // }

            Logger.LogInfo(
                $" Total {unsafeStatePosition.Keys.Count().ToString()} unsafe state found in the environment");
            string unsafeStateDataPath = Path.Combine(resultFolder, $"unsafeSate.json");
            ResultSaver.SaveDictionaryToJson(unsafeStatePosition, unsafeStateDataPath);
            Logger.LogInfo($" Unsafe states data stored at {unsafeStateDataPath}");
            Logger.LogInfo("AIprobe execution completed.");
        }


        private static async Task ProcessEnvironments(List<Environment> environmentsList, int seed, long envCounter)
        {
            var parallelOptions = new ParallelOptions
            {
                MaxDegreeOfParallelism = System.Environment.ProcessorCount
            };

            int totalEnvironments = environmentsList.Count;
            long processedEnvironments = 0; // Track the number of processed environments
            Stopwatch overallStopwatch = Stopwatch.StartNew(); // Measure total elapsed time

            await Parallel.ForEachAsync(environmentsList, parallelOptions, async (env, cancellationToken) =>
            {
                double currentEnvNumber = Interlocked.Increment(ref envCounter);

                string environmentDirPath =
                    $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/{currentEnvNumber}";
                Directory.CreateDirectory(environmentDirPath);

                string environmentFilePath = $"{environmentDirPath}/config.xml";
                await WriteEnvironmentAsync(env, environmentFilePath);

                // Measure time for task generation
                Stopwatch taskGeneratorStopwatch = Stopwatch.StartNew();
                List<Environment> tasks = EnvTaskGenerator.TaskGenerator(env, currentEnvNumber, seed);
                taskGeneratorStopwatch.Stop();
                double taskGenerationTime = taskGeneratorStopwatch.Elapsed.TotalSeconds;

                // Log the time taken for task generation
                Console.WriteLine(
                    $"Environment {currentEnvNumber} task generation took {taskGenerationTime:F2} seconds.");

                int taskCounter = 1;
                await Parallel.ForEachAsync(tasks, async (task, taskCancellationToken) =>
                {
                    string taskFilePath = $"{environmentDirPath}/task{Interlocked.Increment(ref taskCounter)}.xml";
                    await WriteEnvironmentAsync(task, taskFilePath);
                });

                // Increment the processed environments counter
                long completed = Interlocked.Increment(ref processedEnvironments);

                // Print progress every 100 environments
                if (completed % 100 == 0)
                {
                    double elapsedTime = overallStopwatch.Elapsed.TotalSeconds;
                    double averageTimePerEnvironment = elapsedTime / completed;
                    double estimatedTimeRemaining = averageTimePerEnvironment * (totalEnvironments - completed);

                    Console.WriteLine($"Processed: {completed}/{totalEnvironments} environments");
                    Console.WriteLine($"Elapsed Time: {elapsedTime:F2} seconds");
                    Console.WriteLine($"Average Time per Environment: {averageTimePerEnvironment:F2} seconds");
                    Console.WriteLine($"Estimated Time Remaining: {estimatedTimeRemaining:F2} seconds");
                }
            });

            // Stop the overall stopwatch and log the results
            overallStopwatch.Stop();
            Console.WriteLine($"Processing completed!");
            Console.WriteLine($"Total Environments Processed: {totalEnvironments}");
            Console.WriteLine($"Total Processing Time: {overallStopwatch.Elapsed.TotalSeconds:F2} seconds");
        }


        private static void GenrateInstruction(ConcurrentDictionary<Environment, List<Environment>> envTaskMap)
        {
            InstructionChecker instructionChecker = new InstructionChecker();

            foreach (var envTask in envTaskMap)
            {
                Environment initalEnviroment = envTask.Key;

                foreach (var env in envTask.Value)
                {
                    Environment finalEnviroment = env;


                    //List<object[]> taskResults = instructionChecker.InstructionExists(initalEnviroment, finalEnviroment, actionSpace,
                    //     //     config.TimeSettings.InstructionGenerationTime, intialStateHashValue, finalStateHashValue,
                    //     //     out bool instructionExists);
                }
            }
        }

        public static async Task WriteEnvironmentAsync(Environment environment, string resultFilePath)
        {
            try
            {
                // Create the XmlSerializer for the Environment type
                XmlSerializer serializer = new XmlSerializer(typeof(Environment));

                // Serialize the environment to a MemoryStream
                using (var memoryStream = new MemoryStream())
                {
                    serializer.Serialize(memoryStream, environment);
                    memoryStream.Position = 0; // Reset the position to the beginning of the stream

                    // Write the serialized data to the file asynchronously
                    using (var fileStream =
                           new FileStream(resultFilePath, FileMode.Create, FileAccess.Write, FileShare.None))
                    {
                        await memoryStream.CopyToAsync(fileStream);
                    }
                }
            }
            catch (Exception ex)
            {
                // Log or handle exceptions
                LogErrorAndDisplay($"Error writing environment to file: {ex.Message}");
            }
        }

        public static void WriteEnvironment(Environment environment, string resultFilePath)
        {
            try
            {
                XmlSerializer serializer = new XmlSerializer(typeof(Environment));

                // Step 1: Create a custom namespace manager with no namespaces to exclude unwanted xmlns declarations
                XmlSerializerNamespaces namespaces = new XmlSerializerNamespaces();
                namespaces.Add(string.Empty, string.Empty); // This removes the xmlns:xsi and xmlns:xsd

                // Step 2: Serialize the object into an in-memory string with UTF-8 encoding
                string xmlContent;
                using (var stringWriter = new EnvironmentParser.Utf8StringWriter())
                {
                    serializer.Serialize(stringWriter, environment, namespaces); // Use custom namespaces
                    xmlContent = stringWriter.ToString();
                }

                // Step 3: Post-process the serialized XML content to ensure proper spacing
                // Step 3a: Remove any existing space before "/>"
                xmlContent = System.Text.RegularExpressions.Regex.Replace(xmlContent, @"\s*/>", "/>");

                // Step 3b: Add space before self-closing tags where missing
                //xmlContent = System.Text.RegularExpressions.Regex.Replace(xmlContent, @"(?<!\s)/>", " />");

                // Step 4: Compute the SHA-256 hash of the serialized XML content

                // Step 5: Write the serialized XML content to the file with UTF-8 encoding
                using (StreamWriter writer = new StreamWriter(resultFilePath, false, Encoding.UTF8))
                {
                    writer.Write(xmlContent);
                }

                //Logger.LogInfo("Environment object serialized and written to file successfully.");
            }
            catch (Exception ex)
            {
                LogErrorAndDisplay($"Error writing the environment XML file: {ex.Message}");
            }
        }

        public static T DeepCopy<T>(T obj)
        {
            if (obj == null)
            {
                throw new ArgumentNullException(nameof(obj));
            }

            using (MemoryStream ms = new MemoryStream())
            {
                XmlSerializer serializer = new XmlSerializer(typeof(T));
                serializer.Serialize(ms, obj);
                ms.Position = 0;
                return (T)serializer.Deserialize(ms);
            }
        }


        private static void SaveEnvironmentsToCsv(List<Environment> environments, string filePath)
        {
            using (var writer = new System.IO.StreamWriter(filePath))
            {
                // Write header
                writer.WriteLine("EnvironmentName,EnvironmentType,Attributes,Agents,Objects");

                // Write each environment on one line
                foreach (var env in environments)
                {
                    string line = SerializeEnvironmentToOneLine(env);
                    writer.WriteLine(line);
                }
            }
        }


        private static void SetStaticVariable(string aiprobe_root_path, string py_path)
        {
            ConfigParser configParser = new ConfigParser();
            AIprobeConfig config = configParser.ParseConfig();
            if (config == null)
            {
                LogErrorAndDisplay("Failed to parse Aiprobe's configuration file. Exiting...");
                return;
            }
            else
            {
                Console.WriteLine("Config file found ");
            }

            // Set the log file path
            string logFilePath = aiprobe_root_path + "/" + config.LogSettings.LogFilePath;
            //string logFilePath = "/tmp/aiprobe_log.txt";
            
            Console.WriteLine();

            Logger.Initialize(logFilePath);

            pythonScriptFilePath = aiprobe_root_path + "/../" + config.PythonSettings.ScriptFilePath;
            pythonInterpreterPath = py_path; //config.PythonSettings.PythonEnvironment;
            resultFolder = aiprobe_root_path + "/" + config.ResultSetting.ResultFolderPath;
            LogAndDisplay($"Result folder at: {resultFolder}");
            envConfigFile = aiprobe_root_path + "/" + config.FileSettings.InitialEnvironmentFilePath;
            LogAndDisplay($"Initial environment file path: {envConfigFile}");
            seed = config.RandomSettings.Seed;
            LogAndDisplay($"Aiprobe running with seed {seed}");
            taskGenrationTime = config.TimeSettings.TaskGenerationTime;
            LogAndDisplay($"Tasks generation time: {taskGenrationTime}");
            processingTime = config.TimeSettings.Timeout;
            instructionGenerationTime = config.TimeSettings.InstructionGenerationTime;


            Logger.LogInfo(
                $"Action Space File Path: {aiprobe_root_path + "/" + config.FileSettings.ActionSpaceFilePath}");
            ActionSpaceParser actionSpaceParser =
                new ActionSpaceParser(aiprobe_root_path + "/" + config.FileSettings.ActionSpaceFilePath);
            actionSpace = actionSpaceParser.ParseActionSpace();
        }

        private static ConcurrentQueue<Environment> getEnviromentQueue()
        {
            EnvironmentParser intialParser = new EnvironmentParser(envConfigFile);
            Environment initialEnvironment = intialParser.ParseEnvironment();

            //AttributePreprocessor attributePreprocessor = new AttributePreprocessor();
            //attributePreprocessor.ProcessAttributes(initialEnvironment);

            if (initialEnvironment == null)
            {
                LogErrorAndDisplay("Error parsing environment. Please check the input file.");
                return null;
            }


            ConcurrentQueue<Environment> environmentQueue =
                EnvConfigGenerator.GenerateEnvConfigsQueue(initialEnvironment, seed);

            return environmentQueue;
        }


        private static async Task<ConcurrentQueue<(Environment Env, List<Environment> Tasks)>>
            GetEnvironmentTaskQueueAsyncs(
                ConcurrentQueue<Environment> environmentQueue, string resultFolderPath)
        {
            var environmentTaskQueue = new ConcurrentQueue<(Environment Env, List<Environment> Tasks)>();
            int maxDegreeOfParallelism = System.Environment.ProcessorCount;

            // Convert the queue to a list for index-based processing
            var environments = environmentQueue.ToList();

            var tasks = new List<Task>(); // List to hold asynchronous tasks

            EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator();

            await Task.WhenAll(Enumerable.Range(0, environments.Count).Select(async i =>
            {
                Stopwatch envStopwatch = Stopwatch.StartNew(); // Measure time for the current environment
                try
                {
                    var env = environments[i];

                    // Generate tasks for the environment
                    Stopwatch taskGeneratorStopwatch = Stopwatch.StartNew();
                    List<(Environment, Environment)> tasksForEnvironment = envTaskGenerator.GenerateTasksUsingOrthogonalSampling(
                        env, 20, seed: i, resultFolderPath);
                    //List<(Environment, Environment)> tasksForEnvironment = envTaskGenerator.GenerateTasks(env, taskGenrationTime);
                    taskGeneratorStopwatch.Stop();

                    // Save tasks asynchronously in parallel
                    for (int taskIndex = 0; taskIndex < tasksForEnvironment.Count; taskIndex++)
                    {
                        var task = tasksForEnvironment[taskIndex];
                        string environmentFolder = Path.Combine(resultFolderPath, $"Env_{i + 1}");
                        string taskFolder = Path.Combine(environmentFolder, $"Task_{taskIndex + 1}");

                        // Ensure directories exist
                        Directory.CreateDirectory(taskFolder);

                        // File path for the final state
                        string resultFilePath = Path.Combine(taskFolder, "finalState.xml");

                        tasks.Add(WriteEnvironmentAsync(task.Item1,
                            resultFilePath)); // Add each save operation as an asynchronous task
                    }

                    // Enqueue the environment and its tasks
                    //environmentTaskQueue.Enqueue((env, tasksForEnvironment));
                }
                catch (Exception ex)
                {
                    LogErrorAndDisplay($"Error processing environment: {ex.Message}");
                }
                finally
                {
                    envStopwatch.Stop();
                }
            }));

            // Await all the file save tasks
            await Task.WhenAll(tasks);

            return environmentTaskQueue;
        }


        private static async Task<Queue<(string intialPath, string finalPath)>> GetEnvironmentTaskQueueAsync(
            ConcurrentQueue<Environment> environmentQueue, string resultFolderPath)
        {
            var environmentTaskQueue = new Queue<(string intialPath, string finalPath)>();

            // Convert the queue to a list for index-based processing
            var environments = environmentQueue.ToList();

            EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator();

            LogAndDisplay($"Starting sequential processing of {environments.Count} environments...");

            for (int i = 0; i < environments.Count; i++)
            {
                Stopwatch envStopwatch = Stopwatch.StartNew(); // Measure time for the current environment
                try
                {
                    var env = environments[i];
                    
                    LogAndDisplay($"Processing environment {i + 1}/{environments.Count}...");

                    // Generate tasks for the environment
                    Stopwatch taskGeneratorStopwatch = Stopwatch.StartNew();
                    LogAndDisplay($"Generating tasks for environment {i + 1}...");
                    //List<(Environment, Environment)> tasksForEnvironment = envTaskGenerator.GenerateTasks(env, taskGenrationTime);
                    List<(Environment, Environment)> tasksForEnvironment = envTaskGenerator.GenerateTasksUsingOrthogonalSampling(
                        env, 20, seed: i, resultFolderPath);
                    taskGeneratorStopwatch.Stop();
                    LogAndDisplay(
                        $"Generated {tasksForEnvironment.Count} tasks for environment {i + 1} in {taskGeneratorStopwatch.ElapsedMilliseconds} ms.");

                    // Save tasks in parallel
                    var saveTasks = tasksForEnvironment.Select((task, taskIndex) =>
                    {
                        string environmentFolder = Path.Combine(resultFolderPath, $"Env_{i + 1}");
                        string taskFolder = Path.Combine(environmentFolder, $"Task_{taskIndex + 1}");

                        // Ensure directories exist
                        Directory.CreateDirectory(taskFolder);
                        LogAndDisplay($"Created folder: {taskFolder}");

                        // File paths for the initial and final states
                        string initialResultFilePath = Path.Combine(taskFolder, "initialState.xml");
                        string finalResultFilePath = Path.Combine(taskFolder, "finalState.xml");

                        LogAndDisplay(
                            $"Saving task {taskIndex + 1}/{tasksForEnvironment.Count} for environment {i + 1}...");

                        // Write both states and return a combined task
                        var initialStateTask = WriteEnvironmentAsync(task.Item1, initialResultFilePath);
                        var finalStateTask = WriteEnvironmentAsync(task.Item2, finalResultFilePath);

                        environmentTaskQueue.Enqueue((initialResultFilePath, finalResultFilePath));


                        return Task.WhenAll(initialStateTask, finalStateTask); // Combine both tasks
                    });

                    // Wait for all save operations to complete
                    await Task.WhenAll(saveTasks);

                    // Enqueue the environment and its tasks
                    //environmentTaskQueue.Enqueue((env, tasksForEnvironment));
                    LogAndDisplay($"Completed processing for environment {i + 1}.");
                }
                catch (Exception ex)
                {
                    LogErrorAndDisplay($"Error processing environment {i + 1}: {ex.Message}");
                }
                finally
                {
                    envStopwatch.Stop();
                    LogAndDisplay(
                        $"Environment {i + 1} processing completed in {envStopwatch.ElapsedMilliseconds / 100} s.");
                }
            }

            LogAndDisplay("All environments processed sequentially with parallel task saving.");
           
            return environmentTaskQueue;
        }


        
        private static async Task<Queue<(string initialPath, string finalPath)>> GetTasksUsingOrthogonalSamplingAsync(
    ConcurrentQueue<Environment> environmentQueue, string resultFolderPath)
{
    var environmentTaskQueue = new Queue<(string initialPath, string finalPath)>();

    // Convert the queue to a list for index-based processing
    var environments = environmentQueue.ToList();

    LogAndDisplay($"Starting sequential processing of {environments.Count} environments...");

    EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator();
    
    for (int i = 0; i < environments.Count; i++)
    {
        Stopwatch envStopwatch = Stopwatch.StartNew(); // Measure time for the current environment
        try
        {
            var env = environments[i];
            LogAndDisplay($"Processing environment {i + 1}/{environments.Count}...");

            // Generate tasks for the environment using orthogonal sampling
            Stopwatch taskGeneratorStopwatch = Stopwatch.StartNew();
            LogAndDisplay($"Generating tasks for environment {i + 1} using orthogonal sampling...");

            // Adjust parameters for task generation as needed
            int nSamples = 10; // You can customize this based on the number of samples required
            string outputFilePath = Path.Combine(resultFolderPath, $"Env_{i + 1}_orthogonal_samples.csv");

            List<(Environment, Environment)> tasksForEnvironment = envTaskGenerator.GenerateTasksUsingOrthogonalSampling(
                env, nSamples, seed: i, outputFilePath: outputFilePath);

            taskGeneratorStopwatch.Stop();
            LogAndDisplay(
                $"Generated {tasksForEnvironment.Count} tasks for environment {i + 1} in {taskGeneratorStopwatch.ElapsedMilliseconds} ms.");

            // Save tasks in parallel
            var saveTasks = tasksForEnvironment.Select((task, taskIndex) =>
            {
                string environmentFolder = Path.Combine(resultFolderPath, $"Env_{i + 1}");
                string taskFolder = Path.Combine(environmentFolder, $"Task_{taskIndex + 1}");

                // Ensure directories exist
                Directory.CreateDirectory(taskFolder);
                LogAndDisplay($"Created folder: {taskFolder}");

                // File paths for the initial and final states
                string initialResultFilePath = Path.Combine(taskFolder, "initialState.xml");
                string finalResultFilePath = Path.Combine(taskFolder, "finalState.xml");

                LogAndDisplay(
                    $"Saving task {taskIndex + 1}/{tasksForEnvironment.Count} for environment {i + 1}...");

                // Write both states and return a combined task
                var initialStateTask = WriteEnvironmentAsync(task.Item1, initialResultFilePath);
                var finalStateTask = WriteEnvironmentAsync(task.Item2, finalResultFilePath);

                environmentTaskQueue.Enqueue((initialResultFilePath, finalResultFilePath));

                return Task.WhenAll(initialStateTask, finalStateTask); // Combine both tasks
            });

            // Wait for all save operations to complete
            await Task.WhenAll(saveTasks);

            LogAndDisplay($"Completed processing for environment {i + 1}.");
        }
        catch (Exception ex)
        {
            LogErrorAndDisplay($"Error processing environment {i + 1}: {ex.Message}");
        }
        finally
        {
            envStopwatch.Stop();
            LogAndDisplay(
                $"Environment {i + 1} processing completed in {envStopwatch.ElapsedMilliseconds / 1000.0} s.");
        }
    }

    LogAndDisplay("All environments processed sequentially with parallel task saving.");

    return environmentTaskQueue;
}
        
        
        internal static void LogAndDisplay(string text)
        {
            Logger.LogInfo(text);
            Console.WriteLine(text);
        }

        private static void LogErrorAndDisplay(string text)
        {
            Logger.LogError(text);
            Console.WriteLine(text);
        }

        private static string SerializeEnvironmentToOneLine(Environment env)
        {
            // Serialize attributes into a single string
            string attributes = string.Join("; ", env.Attributes?.ConvertAll(attr =>
                $"{attr.Name.Value}={attr.Value.Content} (Type={attr.DataType.Value})") ?? new List<string>());

            // Serialize agents into a single string
            string agents = string.Join("; ", env.Agents?.AgentList?.ConvertAll(agent =>
            {
                string agentAttributes = string.Join(", ", agent.Attributes?.ConvertAll(attr =>
                    $"{attr.Name.Value}={attr.Value.Content} (Type={attr.DataType.Value})") ?? new List<string>());
                return $"Agent_{agent.Id}: [{agentAttributes}]";
            }) ?? new List<string>());

            // Serialize objects into a single string
            string objects = string.Join("; ", env.Objects?.ObjectList?.ConvertAll(obj =>
            {
                string objectAttributes = string.Join(", ", obj.Attributes?.ConvertAll(attr =>
                    $"{attr.Name.Value}={attr.Value.Content} (Type={attr.DataType.Value})") ?? new List<string>());
                return $"Object_{obj.Id} (Type={obj.Type}): [{objectAttributes}]";
            }) ?? new List<string>());

            // Combine all into a single line
            return $"{env.Name},{env.Type},{attributes},{agents},{objects}";
        }
    }
}