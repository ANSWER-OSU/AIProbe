using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class Agents
    {
        [XmlElement("Agent")]
        public List<Agent> AgentList { get; set; }
    }

    public class Agent
    {
        [XmlAttribute("id")]
        public int Id { get; set; }

        [XmlAttribute("type")]
        public string Type { get; set; }

        [XmlElement("Attribute")]
        public List<Attribute> Attributes { get; set; }
    }
    
    
    
    
    
}