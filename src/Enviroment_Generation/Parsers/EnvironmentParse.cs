using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Xml.Serialization;

namespace AIprobe.Parsers
{
    public class EnvironmentParser
    {
        public AIprobe.Models.Environment ParseEnvironment(String _filePath)
        {
            try
            {
                // Read the XML content as a string to compute the hash
                string xmlContent;
                using (StreamReader reader = new StreamReader(_filePath))
                {
                    xmlContent = reader.ReadToEnd();
                }

                // Compute the hash value
                //hashValue = GenerateHash(xmlContent);
                //Logger.LogInfo($"Hash Value: {hashValue}");

                // Deserialize the XML content
                XmlSerializer serializer = new XmlSerializer(typeof(AIprobe.Models.Environment));
                using (StringReader stringReader = new StringReader(xmlContent))
                {
                    AIprobe.Models.Environment environment = (AIprobe.Models.Environment)serializer.Deserialize(stringReader);
                    //Logger.LogInfo("Environment file parsed successfully.");
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