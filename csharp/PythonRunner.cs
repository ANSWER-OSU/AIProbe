using System.Diagnostics;
using System;
using System.IO;
using System.Xml.Serialization;
using AIprobe.Parsers;

namespace AIprobe
{
    public class PythonRunner
    {
        public AIprobe.Models.Environment RunPythonScript(string tempInputFilePath,string tempOutputFilePath, string action,out bool safeCondition)
        {
            

            // Save XML to a temporary file
             //tempInputFilePath = "/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/TEMPLavaEnv.xml";  
             //tempOutputFilePath = "/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/outputTEMPLava.xml";  
          
		 // get the python path
             string py_path = Environment.GetEnvironmentVariable("PYTHON_HOME");
             if (py_path == null)
             {
                Console.WriteLine("Error! please set PYTHON_HOME env variable to point to \"<path-to-aiprobe conda env>/bin/python\" file.");
             }



            string tempXmlFilePath = "TEMPLavaEnv.xml";
            
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = py_path,
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
            
            EnvironmentParser parser = new EnvironmentParser(tempOutputFilePath);
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
