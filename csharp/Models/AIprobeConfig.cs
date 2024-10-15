using System.Xml.Serialization;

namespace AIprobe.Models
{
    [XmlRoot("AIprobeConfig")]
    public class AIprobeConfig
    {
        [XmlElement("LogSettings")]
        public LogSettings LogSettings { get; set; }

        [XmlElement("FileSettings")]
        public FileSettings FileSettings { get; set; }
        
        [XmlElement("TimeSettings")]
        public TimeSettings TimeSettings { get; set; }
        
        [XmlElement("RandomSettings")]
        public RandomSettings RandomSettings { get; set; }
        
        
        [XmlElement("PythonSettings")]
        public PythonSettings PythonSettings { get; set; }
    }

    public class LogSettings
    {
        // [XmlElement("LogLevel")]
        // public string LogLevel { get; set; }

        [XmlElement("LogFilePath")]
        public string LogFilePath { get; set; }
    }

    public class FileSettings
    {
        [XmlElement("InitialEnvironmentFilePath")]
        public string InitialEnvironmentFilePath { get; set; }
        
        [XmlElement("FinalEnviromentFilePath")]
        public string FinalEnviromentFilePath { get; set; }
        
        [XmlElement("ActionSpaceFilePath")]
        public string ActionSpaceFilePath { get; set; }
        
       
        
   
        
        
    }
    
    public class PythonSettings
    {
        [XmlElement("ScriptFilePath")]
        public string ScriptFilePath { get; set; }

        [XmlElement("TempLocation")]
        public string TempLocation { get; set; }

        [XmlElement("PythonEnvironment")]
        public string PythonEnvironment { get; set; }
    }
    
    public class TimeSettings
    {
        [XmlElement("TaskGenerationTime")]
        public int TaskGenerationTime { get; set; } // Time in seconds for task generation

        [XmlElement("InstructionGenerationTime")]
        public int InstructionGenerationTime { get; set; } // Time in seconds for interaction generation
    }


    public class RandomSettings
    {
        [XmlElement("Seed")]
        public int Seed { get; set; }
    }
}