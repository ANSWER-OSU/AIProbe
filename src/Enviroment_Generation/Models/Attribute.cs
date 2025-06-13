using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class Attribute
    {
        [XmlElement("Name")]
        public Name Name { get; set; }

        [XmlElement("Description")]
        public Description Description { get; set; }

        [XmlElement("DataType")]
        public DataType DataType { get; set; }

        [XmlElement("Value")]
        public Value Value { get; set; }

        [XmlElement("Mutable")]
        public Mutable Mutable { get; set; }

        [XmlElement("Constraint")]
        public Constraint Constraint { get; set; }
    }
    
    
    public class Name
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
    }

    public class Description
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
    }

    public class DataType
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
    }

    public class Value
    {
        [XmlAttribute("value")]
        public string Content { get; set; }
    }

    public class Mutable
    {
        [XmlAttribute("value")]
        public bool Value { get; set; }
    }

    public class Constraint
    {
        [XmlAttribute("Min")]
        public string Min { get; set; }

        [XmlAttribute("Max")]
        public string Max { get; set; }

        [XmlAttribute("Values")]
        public string Values { get; set; }

        [XmlAttribute("Choice")]
        public string Choice { get; set; }
    }

}