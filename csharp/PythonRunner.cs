using System.Diagnostics;
using System;
using System.IO;
using System.Xml.Serialization;
using AIprobe.Parsers;

namespace AIprobe
{
    public class PythonRunner
    {
        public AIprobe.Models.Environment RunPythonScript(AIprobe.Models.Environment environment, string filePath, string action,out bool safeCondition )
        {
          
            string xmlData = SerializeEnvironment(environment);

            // Save XML to a temporary file
            string tempInputFilePath = Path.GetTempFileName();  
            string tempOutputFilePath = Path.GetTempFileName();  
            File.WriteAllText(tempInputFilePath, xmlData);
            string tempXmlFilePath = "TEMPLavaEnv.xml";
            
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = Program.pythonInterpreterPath,
                Arguments = $"{Program.pythonScriptFilePath} \"{filePath}\" \"{action}\" \"{tempXmlFilePath}\"",
                RedirectStandardOutput = true, // Capture the output (file path) from Python
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            string updatedXmlFilePath = string.Empty;
            safeCondition = false;
            
            using (Process process = Process.Start(psi))
            {
                using (StreamReader reader = process.StandardOutput)
                {
                    string outputLine;
                    while ((outputLine = reader.ReadLine()) != null)
                    {
                        // Check if the output contains "Condition: safe"
                        if (outputLine.Contains("Condition: safe"))
                        {
                            safeCondition = true;  
                        }
                        else
                        {
                            safeCondition = false;
                        }
                    }
                }

                string error = process.StandardError.ReadToEnd();
                if (!string.IsNullOrEmpty(error))
                {
                    throw new Exception($"Python script error: {error}");
                }

                process.WaitForExit();
            }

            Console.WriteLine("Updated XML file path returned from Python:");
            Console.WriteLine(updatedXmlFilePath);

           
            //string updatedXmlData = File.ReadAllText(updatedXmlFilePath);
            
            EnvironmentParser parser = new EnvironmentParser(tempXmlFilePath);
            return parser.ParseEnvironment();
        }

        private string SerializeEnvironment(AIprobe.Models.Environment environment)
        {
            XmlSerializer serializer = new XmlSerializer(typeof(AIprobe.Models.Environment));
            using (StringWriter stringWriter = new StringWriter())
            {
                serializer.Serialize(stringWriter, environment);
                return stringWriter.ToString();
            }
        }
    }
}
