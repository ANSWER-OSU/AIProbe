using System.Collections.Generic;
using System.Xml.Serialization;
using AIprobe.Models;

public class AgentsModel
{
    [XmlElement("Agent")]
    public List<AgentModel> AgentList { get; set; }
}

public class AgentModel
{
    [XmlAttribute("id")]
    public int Id { get; set; }

    [XmlAttribute("name")]
    public string Name { get; set; }

    [XmlAttribute("type")]
    public string Type { get; set; }

    [XmlElement("Position")]
    public PositionModel Position { get; set; }

    [XmlElement("Direction")]
    public AxisModel Direction { get; set; }
}
