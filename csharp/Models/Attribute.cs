using System.Collections.Generic;
using System.Xml.Serialization;

namespace AIprobe.Models
{
    public class Attribute
    {
        [XmlElement("Name")]
        public Name Name { get; set; }

        [XmlElement("DataType")]
        public DataType DataType { get; set; }

        [XmlElement("Value")]
        public Value Value { get; set; }

        [XmlElement("Min")]
        public Min Min { get; set; }

        [XmlElement("Max")]
        public Max Max { get; set; }

        [XmlElement("Step")]
        public Step Step { get; set; }

        [XmlElement("Mutable")]
        public Mutable Mutable { get; set; }

        [XmlElement("Description")]
        public Description Description { get; set; }

        [XmlElement("ValueList")]
        public ValueList ValueList { get; set; }
        
    }

    public class Name
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
        
        
        public override bool Equals(object obj)
        {
            return obj is Name other && Value == other.Value;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Value);
        }
    }

    public class DataType
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
        
        public override bool Equals(object obj)
        {
            return obj is DataType other && Value == other.Value;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Value);
        }
        
    }

    public class Value
    {
        [XmlAttribute("value")]
        public string ValueData { get; set; }
        
        public override bool Equals(object obj)
        {
            return obj is Value other && ValueData == other.ValueData;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(ValueData);
        }
    }

    public class Min
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
        
        
        public override bool Equals(object obj)
        {
            return obj is Min other && Value == other.Value;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Value);
        }
    }

    public class Max
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
        
        
        
        public override bool Equals(object obj)
        {
            return obj is Max other && Value == other.Value;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Value);
        }
    }

    public class Step
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
        
        
        
        public override bool Equals(object obj)
        {
            return obj is Step other && Value == other.Value;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Value);
        }
    }

    public class Mutable
    {
        [XmlAttribute("value")]
        public bool Value { get; set; }
        
        
        public override bool Equals(object obj)
        {
            return obj is Mutable other && Value == other.Value;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Value);
        }
    }

    public class Description
    {
        [XmlAttribute("value")]
        public string Value { get; set; }
        
        public override bool Equals(object obj)
        {
            return obj is Description other && Value == other.Value;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Value);
        }
    }

    public class ValueList
    {
        [XmlElement("Pair")]
        public List<Pair> Pairs { get; set; }
        
        
        public override bool Equals(object obj)
        {
            if (obj is ValueList other)
            {
                // Compare the count of pairs
                if (Pairs.Count != other.Pairs.Count)
                    return false;

                // Compare each pair
                for (int i = 0; i < Pairs.Count; i++)
                {
                    if (!Pairs[i].Equals(other.Pairs[i]))
                        return false;
                }

                return true;
            }
            return false;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Pairs);
        }
    }

    public class Pair
    {
        [XmlAttribute("key")]
        public string Key { get; set; }

        [XmlAttribute("value")]
        public string Value { get; set; }
        
        
        
        public override bool Equals(object obj)
        {
            return obj is Pair other && Key == other.Key && Value == other.Value;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Key, Value);
        }
    }
}