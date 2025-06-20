using System;
using System.Diagnostics;
using System.Text;
using System.Xml.Serialization;
using AIprobe.Models;
using AIprobe.Parsers;
using AIprobe.TaskGenerator;
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
        public static List<int> seedList = new List<int>();
        private static int taskGenrationTime = 0;
        private static double processingTime = 0;
        private static int instructionGenerationTime = 0;
        private static ActionSpace actionSpace = new ActionSpace();
        public static int bin = 0;
        public static int enviromentSampleConstant = 0;
        public static int taskSampleConstant = 0;
        public static bool isTimeStep = true;

        public static async Task Main(string[] args)
        {
            #region EnvironmentVariable

            SetStaticVariable();

            #endregion

            Console.WriteLine("Reading the config file and setting environment variables...");
            Stopwatch stopwatch = Stopwatch.StartNew();

            CancellationTokenSource cts = new CancellationTokenSource();
            cts.CancelAfter(TimeSpan.FromSeconds(processingTime));

            EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator();
            int totalTasks = 0;
            int instructionFound = 0;
            int totalEnvironment = 0;
            double environmentGenerationTime = 0;
            double taskGenerationTime = 0;

            try
            {
                object lockObj = new();
                // Process each seed sequentially
                await Parallel.ForEachAsync(seedList, async (seed, cancellationToken) =>
                {
                    Stopwatch localStopwatch = Stopwatch.StartNew();

                    // Get the environment queue for the current seed
                    ConcurrentQueue<Environment> environmentQueue = GetEnviromentQueue(envConfigFile, seed);
                    int localEnvironmentCount = environmentQueue.Count;
                    double localEnvironmentGenerationTime = localStopwatch.Elapsed.TotalMilliseconds;

                    // Safely update totals if needed
                    lock (lockObj)
                    {
                        totalEnvironment += localEnvironmentCount;
                        environmentGenerationTime += localEnvironmentGenerationTime;
                    }


                    // Generate tasks asynchronously for the current environment queue
                    localStopwatch.Restart();
                    var envTaskQueue = await GetEnvironmentTaskQueueAsync(environmentQueue, resultFolder, seed);
                    localStopwatch.Stop();

                    int localTaskCount = envTaskQueue.Count;
                    double localTaskGenerationTime = localStopwatch.Elapsed.TotalMilliseconds;

                    lock (lockObj)
                    {
                        environmentGenerationTime += localEnvironmentGenerationTime;
                        totalTasks += localTaskCount;
                    }

                    // Calculate Tomr and print for each seed
                    double tomr = localEnvironmentGenerationTime + localTaskGenerationTime;
                    Console.WriteLine(
                        $"Seed: {seed}, Total Time (Tomr): {tomr} ms, Environments: {localEnvironmentCount}, Tasks: {localTaskCount}");
                });
            }
            catch (OperationCanceledException)
            {
                LogAndDisplay($"Total tasks: {totalTasks}");
                LogAndDisplay($"Total instructions found: {instructionFound}");
                LogAndDisplay("The operation was canceled due to a timeout.");
            }
            finally
            {
                LogAndDisplay($"Total environment: {totalEnvironment}");
                LogAndDisplay($"Total tasks: {totalTasks}");
                LogAndDisplay($"Total generation time: {environmentGenerationTime} ms");
                cts.Dispose();
            }
        }


        private static async Task<ConcurrentQueue<(string initialPath, string finalPath)>> GetEnvironmentTaskQueueAsync(
            ConcurrentQueue<Environment> environmentQueue, string resultFolderPath, int seed)
        {
            var environmentTaskQueue = new ConcurrentQueue<(string initialPath, string finalPath)>();

            var environments = environmentQueue.ToList();
            EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator();

            LogAndDisplay($"Starting parallel processing of {environments.Count} environments...");
            resultFolderPath = $"{resultFolderPath}/{seed}";
            Directory.CreateDirectory(resultFolderPath);

            var environmentProcessingTasks = environments.Select(async (env, index) =>
            {
                Stopwatch envStopwatch = Stopwatch.StartNew();
                try
                {
                    int i = index;
                    LogAndDisplay($"Processing environment {i + 1}/{environments.Count}...");

                    Stopwatch taskGeneratorStopwatch = Stopwatch.StartNew();
                    LogAndDisplay($"Generating tasks for environment {i + 1}...");

                    string environmentFolder = Path.Combine(resultFolderPath, $"Env_{i + 1}");
                    Directory.CreateDirectory(environmentFolder);

                    var tasksForEnvironment = envTaskGenerator.GenerateTask(env, seed, environmentFolder);

                    taskGeneratorStopwatch.Stop();
                    LogAndDisplay(
                        $"Generated {tasksForEnvironment.Count} tasks for environment {i + 1} in {taskGeneratorStopwatch.ElapsedMilliseconds} ms.");

                    // Save tasks in parallel
                    var saveTasks = tasksForEnvironment.Select(async (task, taskIndex) =>
                    {
                        string taskFolder = Path.Combine(environmentFolder, $"Task_{taskIndex + 1}");
                        Directory.CreateDirectory(taskFolder);
                        LogAndDisplay($"Created folder: {taskFolder}");

                        string initialResultFilePath = Path.Combine(taskFolder, "initialState.xml");
                        string finalResultFilePath = Path.Combine(taskFolder, "finalState.xml");

                        LogAndDisplay(
                            $"Saving task {taskIndex + 1}/{tasksForEnvironment.Count} for environment {i + 1}...");

                        var initialStateTask = WriteEnvironmentAsync(task.Item1, initialResultFilePath);
                        var finalStateTask = WriteEnvironmentAsync(task.Item2, finalResultFilePath);

                        await Task.WhenAll(initialStateTask, finalStateTask);

                        environmentTaskQueue.Enqueue((initialResultFilePath, finalResultFilePath));
                    });

                    await Task.WhenAll(saveTasks);

                    LogAndDisplay($"Completed processing for environment {i + 1}.");
                }
                catch (Exception ex)
                {
                    LogErrorAndDisplay($"Error processing environment {index + 1}: {ex.Message}");
                }
                finally
                {
                    envStopwatch.Stop();
                    LogAndDisplay(
                        $"Environment {index + 1} processing completed in {envStopwatch.ElapsedMilliseconds / 100} s.");
                }
            });

            await Task.WhenAll(environmentProcessingTasks);

            LogAndDisplay("All environments processed in parallel with parallel task saving.");

            return environmentTaskQueue;
        }


        private static ConcurrentQueue<Environment> GetEnviromentQueue(string envFilePath, int seed)
        {
            EnvironmentParser intialParser = new EnvironmentParser();
            Environment initialEnvironment = intialParser.ParseEnvironment(envFilePath);

            if (initialEnvironment == null)
            {
                LogErrorAndDisplay("Error parsing environment. Please check the input file.");
                return null;
            }

            ConcurrentQueue<Environment> environmentQueue =
                EnvConfigGenerator.GenerateEnvConfigsQueue(initialEnvironment, seed);

            return environmentQueue;
        }

        private static async Task WriteEnvironmentAsync(Environment environment, string resultFilePath)
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

        private static void SetStaticVariable()
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
            string logFilePath = config.LogSettings.LogFilePath + $"Log{DateTime.Now}.txt";
            //string logFilePath = "/tmp/aiprobe_log.txt";


            Logger.Initialize(logFilePath);

            isTimeStep = config.EnviromentDetails.TimeStepPresent;
            pythonScriptFilePath = config.PythonSettings.ScriptFilePath;
            resultFolder = config.ResultSetting.ResultFolderPath;
            LogAndDisplay($"Result folder at: {resultFolder}");
            envConfigFile = config.FileSettings.EnviromentDataFilePath;
            LogAndDisplay($"Initial environment file path: {envConfigFile}");
            seedList = config.RandomSettings.Seeds;
            foreach (var VARIABLE in seedList)
            {
                LogAndDisplay($"Aiprobe will be running with seed {VARIABLE}");
            }

            bin = config.RandomSettings.Bin;
            LogAndDisplay($"Aiprobe running with bin {bin}");


            Logger.LogInfo($"Action Space File Path: {config.FileSettings.ActionSpaceFilePath}");
            ActionSpaceParser actionSpaceParser = new ActionSpaceParser(config.FileSettings.ActionSpaceFilePath);
            actionSpace = actionSpaceParser.ParseActionSpace();
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
    }
}