using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    /// <summary>
    /// Main model for Environmental Features, containing Physical Properties and Hazards
    /// </summary>
    public class EnvironmentalFeaturesModel
    {
        [XmlElement("PhysicalProperties")]
        public PhysicalPropertiesModel PhysicalProperties { get; set; }

        [XmlElement("Hazards")]
        public HazardsModel Hazards { get; set; }
    }

   /// <summary>
   /// 
   /// </summary>
    public class PhysicalPropertiesModel
    {
        [XmlElement("Property")]
        public List<PropertyModel> Properties { get; set; }
    }

    /// <summary>
    /// 
    /// </summary>
    public class PropertyModel
    {
        [XmlAttribute("name")]
        public string Name { get; set; }

        [XmlAttribute("value")]
        public string Value { get; set; }  // Generic value for storing string, float, etc.

        [XmlAttribute("unit")]
        public string Unit { get; set; }  // Optional for properties that need units (like gravity)

        [XmlAttribute("description")]
        public string Description { get; set; }

        [XmlAttribute("mutable")]
        public bool Mutable { get; set; }

        // Additional attributes for wind or boundary properties
        [XmlAttribute("speed")]
        public float? Speed { get; set; }

        [XmlAttribute("direction")]
        public string Direction { get; set; }

        [XmlAttribute("width")]
        public float? Width { get; set; }

        [XmlAttribute("height")]
        public float? Height { get; set; }

        [XmlAttribute("depth")]
        public float? Depth { get; set; }

        [XmlAttribute("minWidth")]
        public float? MinWidth { get; set; }

        [XmlAttribute("maxWidth")]
        public float? MaxWidth { get; set; }

        [XmlAttribute("minHeight")]
        public float? MinHeight { get; set; }

        [XmlAttribute("maxHeight")]
        public float? MaxHeight { get; set; }

        [XmlAttribute("minDepth")]
        public float? MinDepth { get; set; }

        [XmlAttribute("maxDepth")]
        public float? MaxDepth { get; set; }

        [XmlAttribute("step")]
        public float? Step { get; set; }
    }

   
    /// <summary>
    /// Hazards model that contains a list of hazardous objects
    /// </summary>
    public class HazardsModel
    {
        [XmlElement("Object")]
        public List<ObjectModel> HazardList { get; set; }
    }

    
    /// <summary>
    /// Object model for hazardous objects (e.g., lava, landmines)
    /// </summary>
    public class ObjectModel
    {
        [XmlAttribute("id")]
        public int Id { get; set; }

        [XmlAttribute("name")]
        public string Name { get; set; }

        [XmlAttribute("type")]
        public string Type { get; set; }

        [XmlElement("Position")]
        public PositionModel Position { get; set; }

        [XmlElement("Color")]
        public ColorModel Color { get; set; }

        [XmlElement("Damage")]
        public int? Damage { get; set; }

        public class PositionModel
        {
            [XmlElement("X")]
            public AxisModel X { get; set; }

            [XmlElement("Y")]
            public AxisModel Y { get; set; }

            [XmlElement("Z")]
            public AxisModel Z { get; set; }
        }


        public class AxisModel
        {
            [XmlAttribute("value")]
            public float Value { get; set; }

            [XmlAttribute("min")]
            public float Min { get; set; }

            [XmlAttribute("max")]
            public float Max { get; set; }

            [XmlAttribute("dataType")]
            public string DataType { get; set; }

            [XmlAttribute("step")]
            public float Step { get; set; }

            [XmlAttribute("mutable")]
            public bool Mutable { get; set; }
        }

        public class ColorModel
        {
            [XmlAttribute("value")]
            public string Value { get; set; }

            [XmlAttribute("description")]
            public string Description { get; set; }
        }
    }
}
