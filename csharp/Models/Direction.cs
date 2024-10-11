using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{

    public class Direction
    {
        [XmlElement("Attribute")]
        public Attribute Attribute { get; set; }
    }
}