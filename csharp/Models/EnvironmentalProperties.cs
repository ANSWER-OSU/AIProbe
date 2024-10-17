using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class EnvironmentalProperties
    {
        [XmlElement("Property")]
        public List<Property> Properties { get; set; }
        
        
        public override bool Equals(object obj)
        {
            if (obj is EnvironmentalProperties other)
            {
                if (Properties.Count != other.Properties.Count)
                    return false;

                for (int i = 0; i < Properties.Count; i++)
                {
                    if (!Properties[i].Equals(other.Properties[i]))
                        return false;
                }

                return true;
            }
            return false;
        }

        public override int GetHashCode()
        {
            int hash = 0;
            foreach (var property in Properties)
            {
                hash = HashCode.Combine(hash, property);
            }
            return hash;
        }
        
        
    }

    public class Property
    {
        [XmlAttribute("name")]
        public string Name { get; set; }

        [XmlElement("Attribute")]
        public List<Attribute> Attributes { get; set; }
        
        
        
        
        public override bool Equals(object obj)
        {
            if (obj is Property other)
            {
                // Compare the Name field
                if (Name != other.Name)
                    return false;

                // Check if both properties have the same number of attributes
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
            // Combine hash codes for the Name and each attribute in the list
            int hash = HashCode.Combine(Name);
            foreach (var attribute in Attributes)
            {
                hash = HashCode.Combine(hash, attribute);
            }
            return hash;
        }
        
        
    }
}