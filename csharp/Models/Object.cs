using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class Objects
    {
        [XmlElement("Object")]
        public List<Object> ObjectList { get; set; }
    }

    public class Object
    {
        [XmlAttribute("id")]
        public int Id { get; set; }

        [XmlAttribute("name")]
        public string Name { get; set; }

        [XmlAttribute("type")]
        public string Type { get; set; }

        [XmlElement("Position")]
        public Position Position { get; set; }

        [XmlElement("ObjectAttributes")]
        public ObjectAttributes ObjectAttributes { get; set; }
        
        
        
        public override bool Equals(object obj)
        {
            if (obj is Object other)
            {
                // Compare Id, Name, Type, Position, and ObjectAttributes
                return Id == other.Id &&
                       Name == other.Name &&
                       Type == other.Type &&
                       Position.Equals(other.Position) &&
                       ObjectAttributes.Equals(other.ObjectAttributes);
            }
            return false;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Id, Name, Type, Position, ObjectAttributes);
        }
        
    }
}