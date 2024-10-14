using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class Position
    {
        [XmlElement("Attribute")] 
        public List<Attribute> Attributes { get; set; }
    }
}