using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    /// <summary>
    /// Root model for ActionSpace, either Discrete or Continuous
    /// </summary>
    [XmlRoot("ActionSpace")]
    public class ActionSpaceModel
    {
        [XmlAttribute("type")]
        public string Type { get; set; }

        [XmlElement("Action")]
        public List<ActionModel> Actions { get; set; }
    }

  
    /// <summary>
    /// Model for a generic action, can be Discrete or Continuous
    /// </summary>
    public class ActionModel
    {
        [XmlAttribute("id")]
        public int Id { get; set; }

        [XmlAttribute("name")]
        public string Name { get; set; }

        [XmlAttribute("description")]
        public string Description { get; set; }

        // Discrete Action Value
        [XmlElement("Value")]
        public int? Value { get; set; }  // Nullable int for Discrete Action

        // Continuous Action Range
        [XmlElement("Range")]
        public RangeModel Range { get; set; }  // For Continuous Action
    }

    /// <summary>
    /// Model for continuous action range (Min, Max, Step)
    /// </summary>
    public class RangeModel
    {
        [XmlElement("Min")]
        public float Min { get; set; }

        [XmlElement("Max")]
        public float Max { get; set; }

        [XmlElement("Step")]
        public float Step { get; set; }
    }
}
