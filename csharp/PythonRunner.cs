using System.Diagnostics;
using System;
using System.IO;
using System.Xml.Serialization;
using AIprobe.Parsers;

namespace AIprobe
{
    public class PythonRunner
    {
        public AIprobe.Models.Environment RunPythonScript(string filePath, string action,out bool safeCondition,out string hashValue)
        {
            

            // Save XML to a temporary file
            string tempInputFilePath = "/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/TEMPLavaEnv.xml";  
            string tempOutputFilePath = "/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/outputTEMPLava.xml";  
            
            string tempXmlFilePath = "TEMPLavaEnv.xml";
            
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = Program.pythonInterpreterPath,
                Arguments = $"{Program.pythonScriptFilePath} \"{tempInputFilePath}\" \"{action}\" \"{tempOutputFilePath}\"",
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
                        else if(outputLine.Contains("Condition: unsafe"))
                        {
                            safeCondition = false;
                        }
                        
                        Console.WriteLine(outputLine);
                    }
                }

                string error = process.StandardError.ReadToEnd();
                if (!string.IsNullOrEmpty(error))
                {
                      throw new Exception($"Python script error: {error}");
                }

                process.WaitForExit();
            }
            
           
            //string updatedXmlData = File.ReadAllText(updatedXmlFilePath);
            
            EnvironmentParser parser = new EnvironmentParser("/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/outputTEMPLava.xml");
            return parser.ParseEnvironment(out hashValue);
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
