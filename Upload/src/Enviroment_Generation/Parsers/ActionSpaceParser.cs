using System;
using System.IO;
using System.Xml.Serialization;
using AIprobe.Models;

namespace AIprobe.Parsers
{
    public class ActionSpaceParser
    {
        private string _filePath;

        public ActionSpaceParser(string filePath)
        {
            _filePath = filePath;
        }

  
        /// <summary>
        /// To parse the Action space XML
        /// </summary>
        /// <returns> ActionSpaceModel object</returns>
        public ActionSpace ParseActionSpace()
        {
            try
            {
                // Create an XmlSerializer for the ActionSpaceModel
                XmlSerializer serializer = new XmlSerializer(typeof(ActionSpace));

                // Open the XML file and deserialize it
                using (StreamReader reader = new StreamReader(_filePath))
                {
                    // Deserialize the XML into an ActionSpaceModel object
                    ActionSpace actionSpace = (ActionSpace)serializer.Deserialize(reader);

                    // Return the parsed ActionSpaceModel object
                    return actionSpace;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error parsing the XML file: {ex.Message}");
                return null;
            }
        }
    }
}
