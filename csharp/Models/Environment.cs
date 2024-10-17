using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    [XmlRoot("Environment")]
    public class Environment
    {
        [XmlAttribute("name")]
        public string Name { get; set; }

        [XmlAttribute("type")]
        public string Type { get; set; }

        [XmlElement("Agents")]
        public Agents Agents { get; set; }

        [XmlElement("Objects")]
        public Objects Objects { get; set; }

        [XmlElement("EnvironmentalProperties")]
        public EnvironmentalProperties EnvironmentalProperties { get; set; }
        
        
        
    }
}