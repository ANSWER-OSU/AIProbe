using System;
using System.Xml.Serialization;
//using AIprobe.EnvironmentGenerator;
using AIprobe.Logging;
using AIprobe.Models;
using AIprobe.Parsers;
using AIprobe.TaskGenerator;
using AIprobe.InstructionGenerator;
using Action = System.Action;
using Environment = AIprobe.Models.Environment;

namespace AIprobe
{
    internal class Program
    {
        public static string envConfigFile = String.Empty;
        public static string pythonScriptFilePath = String.Empty;
        public static string pythonInterpreterPath = String.Empty;
        public static string  resultFolder = String.Empty;
        public static string tempFolder = String.Empty;
        
        
        static void Main(string[] args)
        {
		
	    // get the root path
	     string aiprobe_root_path = System.Environment.GetEnvironmentVariable("AIPROBE_HOME");
	     if (aiprobe_root_path == null)
             {
            	Console.WriteLine("Error! please set AIPROBE_HOME env variable to point to \"<path-to>AIProbe/csharp\" directory.");
             }
     	// get the python pathSystem
             string py_path = System.Environment.GetEnvironmentVariable("PYTHON_HOME");
             if (py_path == null)
             {
                Console.WriteLine("Error! please set PYTHON_HOME env variable to point to \"<path-to-aiprobe conda env>/bin/python\" file.");
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
            Logger.Initialize(logFilePath);
            
            Logger.LogInfo("Starting AIprobe...");
            pythonScriptFilePath = aiprobe_root_path + "/../" + config.PythonSettings.ScriptFilePath;
            pythonInterpreterPath = py_path; //config.PythonSettings.PythonEnvironment;
            resultFolder = aiprobe_root_path + "/" + config.ResultSetting.ResultFolderPath;

            // Parse the initial environment file
            Console.WriteLine(resultFolder);
            envConfigFile = aiprobe_root_path + "/" + config.FileSettings.InitialEnvironmentFilePath;
            Logger.LogInfo($"Initial Environment File Path: {config.FileSettings.InitialEnvironmentFilePath}");
            Console.WriteLine(envConfigFile);
            EnvironmentParser intialParser = new EnvironmentParser(envConfigFile);
            AIprobe.Models.Environment initialEnvironment = intialParser.ParseEnvironment();

            
            if (initialEnvironment == null)
            {
                Console.WriteLine("Error parsing environment. Please check the input file.");
		Logger.LogError("Error parsing environment. Please check the input file.");
                return;
            }
           
            
            Logger.LogInfo("Initial Environment parsed successfully.");
            
            // Parse the action space of the Environment.
            Logger.LogInfo($"Action Space File Path: {aiprobe_root_path + "/" + config.FileSettings.ActionSpaceFilePath}");
            ActionSpaceParser actionSpaceParser = new ActionSpaceParser(aiprobe_root_path + "/" + config.FileSettings.ActionSpaceFilePath);
            ActionSpace  actionSpace = actionSpaceParser.ParseActionSpace();
            
            
            
            //EnvConfigGenerator envConfigGenerator = new EnvConfigGenerator();
            EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator(config.RandomSettings.Seed);
            InstructionChecker instructionChecker = new InstructionChecker();
            
            // generating new env from inital env 
            //List<AIprobe.Models.Environment> environments =  envConfigGenerator.GenerateEnvConfigs(initialEnvironment,config.RandomSettings.Seed);

            //var env = initialEnvironment;
            
            //foreach(AIprobe.Models.Environment env in environments)
            {
                string resultEnviromentPath = resultFolder;
                // Generating new tasks list
                List<(AIprobe.Models.Environment,Environment)> tasksList = envTaskGenerator.GenerateTasks(initialEnvironment,config.TimeSettings.TaskGenerationTime);

                // foreach ( var task  in tasksList)
                // {
                
                int tasksCount =0;
                int totaltaskachieved = 0;
                foreach (var task in tasksList)
                {
                    
                    string taskFolder = Path.Combine(resultEnviromentPath, $"Task_{tasksCount}");
                    string initalStateTaskPath = Path.Combine(taskFolder,"initialState.xml");
                    string finalStateTaskPath = Path.Combine(taskFolder,"finalState.xml");
                    string instructionsPath = Path.Combine(taskFolder,"AIprobe.json");
                    tempFolder = Path.Combine(taskFolder, $"Temp_{tasksCount}");
                    Directory.CreateDirectory(tempFolder);
                    Directory.CreateDirectory(Path.GetDirectoryName(initalStateTaskPath));
                    Directory.CreateDirectory(Path.GetDirectoryName(tempFolder));
                        
                    File.Create(initalStateTaskPath).Dispose();
                    File.Create(finalStateTaskPath).Dispose();
                    
                    EnvironmentParser initalStateTaskPasser = new EnvironmentParser(initalStateTaskPath);
                    initalStateTaskPasser.WriteEnvironment(task.Item1,out string intialStateHashValue);
                    // //
                    EnvironmentParser finalStateTaskPasser = new EnvironmentParser(finalStateTaskPath);
                    finalStateTaskPasser.WriteEnvironment(task.Item2,out string finalStateHashValue);
                    
                    
                    
                    // EnvironmentParser initalxml = new EnvironmentParser("/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/Task_0/initialState.xml");
                    // AIprobe.Models.Environment initialEnvironmentxml = initalxml.ParseEnvironment(out string initalEnviromentHashValuexml);
                    //
                    // EnvironmentParser finalxml = new EnvironmentParser("/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/Task_0/finalState.xml");
                    // AIprobe.Models.Environment finaEnvironmentxml = finalxml.ParseEnvironment(out string finalEnviromentHashValuexml);
                    //
                    
                    List<object[]> taskResults = instructionChecker.InstructionExists(task.Item1,task.Item2,actionSpace,config.TimeSettings.InstructionGenerationTime,intialStateHashValue,finalStateHashValue,out bool instructionExists);
                    ResultSaver.SaveTaskResults(taskResults,instructionsPath);
                    if (instructionExists)
                    {
                        totaltaskachieved++;
                        Logger.LogInfo($"Task {tasksCount} instructions found saved to {taskFolder}");
                    }
                    
                    tasksCount++;
                    
                }
                
                Logger.LogInfo($"Total task achieved {totaltaskachieved} from {tasksList.Count} task.");
                
        
                
                    // List<object[]> taskResults = instructionChecker.InstructionExists(initialEnvironment,tasksList[0],actionSpace,config.TimeSettings.InstructionGenerationTime,initalEnviromentHashValue);
                    //
                    // ResultSaver.SaveTaskResults(taskResults,"/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/AIprobe.json");
                    //

            }
            
            Logger.LogInfo("AIprobe execution completed.");
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

        
    }
    
   
}
