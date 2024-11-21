using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class Objects
    {
        [XmlElement("Object")]
        public List<Object> ObjectList { get; set; }
    }

    public class Object
    {
        [XmlAttribute("id")]
        public int Id { get; set; }

        [XmlAttribute("type")]
        public string Type { get; set; }

        [XmlElement("Attribute")]
        public List<Attribute> Attributes { get; set; }
    }
}