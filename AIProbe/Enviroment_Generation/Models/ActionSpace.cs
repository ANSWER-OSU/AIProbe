using System.Xml.Serialization;

namespace AIprobe.Models
{
    
    [XmlRoot("ActionSpace")]
    public class ActionSpace
    {
        [XmlAttribute("type")]
        public string Type { get; set; }

        [XmlElement("Actions")]
        public Actions Actions { get; set; }
    }
    public class Actions
    {
        [XmlElement("Action")]
        public List<Action> ActionList { get; set; }
    }

    public class Action
    {
        [XmlAttribute("id")]
        public int Id { get; set; }

        [XmlAttribute("name")]
        public string Name { get; set; }

        [XmlElement("Description")]
        public string Description { get; set; }
    }
    
    
}

