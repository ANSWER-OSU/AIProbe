using System;

using AIprobe.EnvironmentGenerator;
using AIprobe.Logging;
using AIprobe.Models;
using AIprobe.Parsers;
using AIprobe.TaskGenerator;
using AIprobe.InstructionGenerator;

namespace AIprobe
{
    internal class Program
    {
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
            
            

            // Parse the initial environment file
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
            
            
            EnvConfigGenerator envConfigGenerator = new EnvConfigGenerator();
            EnvTaskGenerator envTaskGenerator = new EnvTaskGenerator(config.RandomSettings.Seed);
            InstructionChecker instructionChecker = new InstructionChecker();
            
            // generating new env from inital env 
            List<AIprobe.Models.Environment> environments =  envConfigGenerator.GenerateEnvConfigs(initialEnvironment);

            var env = initialEnvironment;
            //foreach(AIprobe.Models.Environment env in environments)
            {
                // Generating new tasks list
                List<AIprobe.Models.Environment> tasksList = envTaskGenerator.GenerateTasks(env,config.TimeSettings.TaskGenerationTime);

                foreach (AIprobe.Models.Environment task  in tasksList)
                {
                    List<object[]> taskResults = instructionChecker.InstructionExists(env,task,config.TimeSettings.InstructionGenerationTime);
                    ResultSaver.SaveTaskResults(taskResults,config.LogSettings.LogFilePath);
                }

            }
            
            Logger.LogInfo("AIprobe execution completed.");
        }
        
    }
    
   
}