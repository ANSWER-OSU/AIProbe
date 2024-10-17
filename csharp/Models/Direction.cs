using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{

    public class Direction
    {
        [XmlElement("Attribute")]
        public List<Attribute>  Attributes { get; set; }
        
        
        
        public override bool Equals(object obj)
        {
            if (obj is Direction other)
            {
                // Check if both directions have the same number of attributes
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

        // Override GetHashCode method for proper hashing
        public override int GetHashCode()
        {
            // Combine hash codes of all attributes
            int hash = 0;
            foreach (var attribute in Attributes)
            {
                hash = HashCode.Combine(hash, attribute);
            }
            return hash;
        }
    }
    
    
}