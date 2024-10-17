using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class Position
    {
        [XmlElement("Attribute")] 
        public List<Attribute> Attributes { get; set; }
        
        public override bool Equals(object obj)
        {
            if (obj is Position other)
            {
                // Check if both positions have the same number of attributes
                if (Attributes.Count != other.Attributes.Count)
                    return false;

                // Compare each attribute in the list
                for (int i = 0; i < Attributes.Count; i++)
                {
                    if (!Attributes[i].Equals(other.Attributes[i]))
                        return false;
                }

                return true;
            }
            return false;
        }

        public override int GetHashCode()
        {
            // Use a combination of hash codes from all attributes
            return HashCode.Combine(Attributes);
        }
        
    }
}