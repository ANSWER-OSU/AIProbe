using System;
using System.IO;
using System.Xml.Serialization;

namespace AIprobe
{
    /// <summary>
    /// This class handles the parsing of the XML file into the EnvironmentModel object
    /// </summary>
    public class EnvironmentParser
    {
        private string _filePath;

        
        public EnvironmentParser(string filePath)
        {
            _filePath = filePath;
        }

        /// <summary>
        /// Method to parse the XML file and return the EnvironmentModel object
        /// </summary>
        /// <returns> Environment object </returns>
        public EnvironmentModel ParseEnvironment()
        {
            try
            {
                // Create an XmlSerializer for the EnvironmentModel
                XmlSerializer serializer = new XmlSerializer(typeof(EnvironmentModel));

                // Open the XML file and deserialize it
                using (StreamReader reader = new StreamReader(_filePath))
                {
                    // Deserialize the XML into an EnvironmentModel object
                    EnvironmentModel environment = (EnvironmentModel)serializer.Deserialize(reader);

                    // Return the parsed object
                    return environment;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error parsing the Environment XML file: {ex.Message}");
                return null;
            }
        }
    }
}
