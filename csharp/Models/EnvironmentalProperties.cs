using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class EnvironmentalProperties
    {
        [XmlElement("Property")]
        public List<Property> Properties { get; set; }
    }

    public class Property
    {
        [XmlAttribute("name")]
        public string Name { get; set; }

        [XmlElement("Attribute")]
        public List<Attribute> Attributes { get; set; }
    }
}