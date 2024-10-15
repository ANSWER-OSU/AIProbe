using System;
using System.Xml.Serialization;
using AIprobe.EnvironmentGenerator;
using AIprobe.Logging;
using AIprobe.Models;
using AIprobe.Parsers;
using AIprobe.TaskGenerator;
using AIprobe.InstructionGenerator;
using Action = System.Action;

namespace AIprobe
{
    internal class Program
    {
        public static string envConfigFile = String.Empty;
        public static string pythonScriptFilePath = String.Empty;
        public static string pythonInterpreterPath = String.Empty;
        
        static void Main(string[] args)
        {
            // Set the log file path
            string logFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "AIprobeLog.txt");
            Logger.Initialize(logFilePath);

            Logger.LogInfo("Starting AIprobe...");
 
            // Parse the AIprobe configuration file
            ConfigParser configParser = new ConfigParser();
            AIprobeConfig config = configParser.ParseConfig();
            if (config == null)
            {
                Logger.LogError("Failed to parse Aiprobe's configuration file. Exiting...");
                return;
            }

            pythonScriptFilePath = config.PythonSettings.ScriptFilePath;
            pythonInterpreterPath = config.PythonSettings.PythonEnvironment;
            
            

            // Parse the initial environment file
            envConfigFile = config.FileSettings.InitialEnvironmentFilePath;
            Logger.LogInfo($"Initial Environment File Path: {config.FileSettings.InitialEnvironmentFilePath}");
            Console.WriteLine(config.FileSettings.InitialEnvironmentFilePath);
            EnvironmentParser intialParser = new EnvironmentParser(config.FileSettings.InitialEnvironmentFilePath);
            AIprobe.Models.Environment initialEnvironment = intialParser.ParseEnvironment();

            if (initialEnvironment != null)
            {
                Logger.LogInfo("Initial Environment parsed successfully.");
            }
            else
            {
                Logger.LogError("Error parsing environment. Please check the input file.");
            }
            
            
            
            // Parse the action space of the Environment.
            Logger.LogInfo($"Action Space File Path: {config.FileSettings.ActionSpaceFilePath}");
            ActionSpaceParser actionSpaceParser = new ActionSpaceParser(config.FileSettings.ActionSpaceFilePath);
            ActionSpace  actionSpace = actionSpaceParser.ParseActionSpace();
            
            
            
            EnvConfigGenerator envConfigGenerator = new EnvConfigGenerator();
            EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator(config.RandomSettings.Seed);
            InstructionChecker instructionChecker = new InstructionChecker();
            
            // generating new env from inital env 
            List<AIprobe.Models.Environment> environments =  envConfigGenerator.GenerateEnvConfigs(initialEnvironment);

            //var env = initialEnvironment;
            var env = DeepCopy(initialEnvironment);
            //foreach(AIprobe.Models.Environment env in environments)
            {
                // Generating new tasks list
                List<AIprobe.Models.Environment> tasksList = envTaskGenerator.GenerateTasks(env,config.TimeSettings.TaskGenerationTime);

                foreach ( var task  in tasksList)
                {
                    
                    List<object[]> taskResults = instructionChecker.InstructionExists(initialEnvironment,task,actionSpace,config.TimeSettings.InstructionGenerationTime);
                    
                    ResultSaver.SaveTaskResults(taskResults,"/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles");
                }

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