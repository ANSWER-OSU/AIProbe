using System;
using System.IO;
using System.Xml.Serialization;
using AIprobe.Models;
using Environment = System.Environment;

namespace AIprobe.Parsers
{
    public class ConfigParser
    {
        private readonly string _configFileName = "AIprobeConfig.xml";

        public string FindConfigFilePath()
        {
            string baseDirectory = AppDomain.CurrentDomain.BaseDirectory;
            string configFilePath = Path.Combine(baseDirectory, _configFileName);

            if (File.Exists(configFilePath))
            {
                Console.WriteLine("config file path used by AIProbe ###############################################");
                Console.WriteLine(configFilePath);
                return configFilePath;
            }

            string configSubDir = Path.Combine(baseDirectory, "config", _configFileName);
            if (File.Exists(configSubDir))
            {
                return configSubDir;
            }

            string envConfigPath = Environment.GetEnvironmentVariable("AIprobeConfigPath");
            if (!string.IsNullOrEmpty(envConfigPath) && File.Exists(envConfigPath))
            {
                return envConfigPath;
            }

            Logger.LogError("Config file not found.");
            throw new FileNotFoundException("AIprobeConfig.xml could not be found.");
        }

        public AIprobeConfig ParseConfig()
        {
            string configFilePath = FindConfigFilePath();

            try
            {
                XmlSerializer serializer = new XmlSerializer(typeof(AIprobeConfig));
                using (StreamReader reader = new StreamReader(configFilePath))
                {
                    AIprobeConfig config = (AIprobeConfig)serializer.Deserialize(reader);
                    //Logger.LogInfo("Configuration file parsed successfully.");
                    return config;
                }
            }
            catch (Exception ex)
            {
                Logger.LogError($"Error parsing the AIprobeConfig XML file: {ex.Message}");
                return null;
            }
        }
    }
}