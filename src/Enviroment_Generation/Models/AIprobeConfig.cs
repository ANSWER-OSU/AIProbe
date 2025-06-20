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
        
        // [XmlElement("TimeSettings")]
        // public TimeSettings TimeSettings { get; set; }
        
        [XmlElement("EnviromentDetails")]
        public EnviromentDetails EnviromentDetails { get; set; }
        
        [XmlElement("RandomSettings")]
        public RandomSettings RandomSettings { get; set; }
        
        
        [XmlElement("PythonSettings")]
        public PythonSettings PythonSettings { get; set; }
        
        [XmlElement("ResultSetting")]
        public ResultSetting ResultSetting { get; set; }
        
    }

    public class ResultSetting
    {
        [XmlElement("ResultFolderPath")]
        public string ResultFolderPath { get; set; }
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
        [XmlElement("EnviromentDataFilePath")]
        public string EnviromentDataFilePath { get; set; }
        
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
        public int InstructionGenerationTime { get; set; }
        
        [XmlElement("Timeout")]
        public double Timeout { get; set; }
    }

    public class RandomSettings
    {
        [XmlArray("Seeds")]
        [XmlArrayItem("Seed")]
        public List<int> Seeds { get; set; } = new List<int>();
        
        
        [XmlElement("Bin")]
        public int Bin { get; set; }
        
        [XmlElement("EnviromentSampleConstant")]
        public int EnviromentSampleConstant { get; set; }
        
        [XmlElement("TaskSampleConstant")]
        public int TaskSampleConstant  {get; set; }
        
    }

    public class EnviromentDetails
    {
        [XmlElement("TimeStepPresent")]
        public bool TimeStepPresent{ get; set; }
        
        [XmlElement("FinalState")]
        public bool FinalState{ get; set; }
    }
}