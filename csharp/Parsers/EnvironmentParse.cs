using System;
using System.IO;
using System.Xml.Serialization;
using AIprobe.Logging;
using AIprobe.Models;

namespace AIprobe.Parsers
{
    public class EnvironmentParser
    {
        private readonly string _filePath;

        public EnvironmentParser(string filePath)
        {
            _filePath = filePath;
        }

        public AIprobe.Models.Environment ParseEnvironment()
        {
            try
            {
                XmlSerializer serializer = new XmlSerializer(typeof(AIprobe.Models.Environment));
                using (StreamReader reader = new StreamReader(_filePath))
                {
                    AIprobe.Models.Environment environment = (AIprobe.Models.Environment)serializer.Deserialize(reader);
                    Logger.LogInfo("Environment file parsed successfully.");
                    return environment;
                }
            }
            catch (Exception ex)
            {
                Logger.LogError($"Error parsing the environment XML file: {ex.Message}");
                return null;
            }
        }
    }
}