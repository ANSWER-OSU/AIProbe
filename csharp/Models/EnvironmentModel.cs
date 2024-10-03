using System.Xml.Serialization;
using AIprobe.Models;

[XmlRoot("Environment")]
public class EnvironmentModel
{
    [XmlAttribute("name")]
    public string Name { get; set; }

    [XmlAttribute("type")]
    public string Type { get; set; }

    [XmlElement("Agents")]
    public AgentsModel Agents { get; set; }

    [XmlElement("Objects")]
    public ObjectsModel Objects { get; set; }

    [XmlElement("EnvironmentFeatures")]
    public EnvironmentalFeaturesModel EnvironmentFeatures { get; set; }
}
