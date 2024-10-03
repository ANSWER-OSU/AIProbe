using System.Collections.Generic;
using System.Xml.Serialization;


public class ObjectsModel
{
    [XmlElement("Object")]
    public List<ObjectModel> ObjectList { get; set; }
}

/// <summary>
/// ObjectModel class that defines each object in the environment (like Wall, Door)
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

    [XmlElement("Impassable")]
    public ImpassableModel Impassable { get; set; }

    [XmlElement("Locked")]
    public bool? Locked { get; set; }  // Optional

    [XmlElement("Open")]
    public bool? Open { get; set; }    // Optional
}


public class ColorModel
{
    [XmlAttribute("value")]
    public string Value { get; set; }

    [XmlAttribute("description")]
    public string Description { get; set; }
}

/// <summary>
/// 
/// </summary>
public class ImpassableModel
{
    [XmlAttribute("value")]
    public bool Value { get; set; }

    [XmlAttribute("description")]
    public string Description { get; set; }
}
