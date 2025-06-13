using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class ObjectAttributes
    {
        [XmlElement("Attribute")]
        public List<Attribute> Attributes { get; set; }
    }
}