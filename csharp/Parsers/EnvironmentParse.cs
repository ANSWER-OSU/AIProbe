using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
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
        
        public static string GenerateHash(string xmlContent)
        {
            using (SHA256 sha256 = SHA256.Create())
            {
                byte[] xmlBytes = Encoding.UTF8.GetBytes(xmlContent);
                byte[] hashBytes = sha256.ComputeHash(xmlBytes);
                StringBuilder hashBuilder = new StringBuilder();
                foreach (byte b in hashBytes)
                {
                    hashBuilder.Append(b.ToString("x2")); // Converts byte to hex string
                }
                return hashBuilder.ToString();
            }
        }

        public AIprobe.Models.Environment ParseEnvironment()
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
                //hashValue = null;
                return null;
            }
        }
        
        public bool WriteEnvironment(AIprobe.Models.Environment environment, out string hashValue)
        {
            try
            {
                XmlSerializer serializer = new XmlSerializer(typeof(AIprobe.Models.Environment));

                // Step 1: Create a custom namespace manager with no namespaces to exclude unwanted xmlns declarations
                XmlSerializerNamespaces namespaces = new XmlSerializerNamespaces();
                namespaces.Add(string.Empty, string.Empty); // This removes the xmlns:xsi and xmlns:xsd

                // Step 2: Serialize the object into an in-memory string with UTF-8 encoding
                string xmlContent;
                using (var stringWriter = new Utf8StringWriter())
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
                hashValue = GenerateHash(xmlContent);

                // Step 5: Write the serialized XML content to the file with UTF-8 encoding
                using (StreamWriter writer = new StreamWriter(_filePath, false, Encoding.UTF8))
                {
                    writer.Write(xmlContent);
                }

                //Logger.LogInfo("Environment object serialized and written to file successfully.");
                return true;
            }
            catch (Exception ex)
            {
                Logger.LogError($"Error writing the environment XML file: {ex.Message}");
                hashValue = null;
                return false;
            }
        }

// Subclass StringWriter to enforce UTF-8 encoding
        public class Utf8StringWriter : StringWriter
        {
            public override Encoding Encoding => Encoding.UTF8;
        }

    }
}