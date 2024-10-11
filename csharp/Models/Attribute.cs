using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class Attribute
    {
        [XmlElement("Name")]
        public Name Name { get; set; }

        [XmlElement("DataType")]
        public DataType DataType { get; set; }

        [XmlElement("Value")]
        public Value Value { get; set; }

        [XmlElement("Min")]
        public Min Min { get; set; }

        [XmlElement("Max")]
        public Max Max { get; set; }

        [XmlElement("Step")]
        public Step Step { get; set; }

        [XmlElement("Mutable")]
        public Mutable Mutable { get; set; }

        [XmlElement("Description")]
        public Description Description { get; set; }

        [XmlElement("ValueList")]
        public ValueList ValueList { get; set; }
    }

    public class Name
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
        public string ValueData { get; set; }
    }

    public class Min
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
    }

    public class Max
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
    }

    public class Step
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
    }

    public class Mutable
    {
        [XmlAttribute("value")]
        public bool Value { get; set; }
    }

    public class Description
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
    }

    public class ValueList
    {
        [XmlElement("Pair")]
        public List<Pair> Pairs { get; set; }
    }

    public class Pair
    {
        [XmlAttribute("key")]
        public string Key { get; set; }

        [XmlAttribute("value")]
        public string Value { get; set; }
    }
}