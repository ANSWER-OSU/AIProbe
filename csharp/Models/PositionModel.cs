using System.Xml.Serialization;

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
