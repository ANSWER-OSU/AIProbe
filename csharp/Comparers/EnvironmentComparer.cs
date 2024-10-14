// using AIprobe.Models;
// using System.Linq;
// using Attribute = AIprobe.Models.Attribute;
// using Environment = AIprobe.Models.Environment;
// using Object = AIprobe.Models.Object;
//
// namespace AIprobe.Comparers
// {
//     public static class EnvironmentComparer
//     {
//         public static bool AreEnvironmentsEqual(Environment env1, Environment env2)
//         {
//             // Check if environment names and types match
//             if (env1?.Name != env2?.Name || env1?.Type != env2?.Type)
//                 return false;
//
//             // Compare agents and objects list count
//             if (env1?.Agents?.AgentList?.Count != env2?.Agents?.AgentList?.Count || 
//                 env1?.Objects?.ObjectList?.Count != env2?.Objects?.ObjectList?.Count)
//                 return false;
//
//             // Compare agents
//             if (!env1.Agents.AgentList.SequenceEqual(env2.Agents.AgentList, new AgentComparer()))
//                 return false;
//
//             // Compare objects
//             if (!env1.Objects.ObjectList.SequenceEqual(env2.Objects.ObjectList, new ObjectComparer()))
//                 return false;
//
//             return true;
//         }
//
//         private class AgentComparer : IEqualityComparer<Agent>
//         {
//             public bool Equals(Agent agent1, Agent agent2)
//             {
//                 if (agent1 == null || agent2 == null) return false;
//
//                 // Compare agent properties (ID, Name, Type) and position attributes
//                 return agent1.Id == agent2.Id && 
//                        agent1.Name == agent2.Name && 
//                        agent1.Type == agent2.Type &&
//                        agent1.Position.Attributes.SequenceEqual(agent2.Position.Attributes, new AttributeComparer()) &&
//                        new AttributeComparer().Equals(agent1.Direction.Attribute, agent2.Direction.Attribute);
//             }
//
//             public int GetHashCode(Agent agent)
//             {
//                 return agent.Id.GetHashCode();
//             }
//         }
//
//         private class ObjectComparer : IEqualityComparer<Object>
//         {
//             public bool Equals(Object obj1, Object obj2)
//             {
//                 if (obj1 == null || obj2 == null) return false;
//
//                 // Compare object properties (ID, Name, Type) and position and attributes
//                 return obj1.Id == obj2.Id &&
//                        obj1.Name == obj2.Name &&
//                        obj1.Type == obj2.Type &&
//                        obj1.Position.Attributes.SequenceEqual(obj2.Position.Attributes, new AttributeComparer()) &&
//                        obj1.ObjectAttributes.Attributes.SequenceEqual(obj2.ObjectAttributes.Attributes, new AttributeComparer());
//             }
//
//             public int GetHashCode(Object obj)
//             {
//                 return obj.Id.GetHashCode();
//             }
//         }
//
//         private class AttributeComparer : IEqualityComparer<Attribute>
//         {
//             public bool Equals(Attribute attr1, Attribute attr2)
//             {
//                 // Compare all relevant fields of an attribute
//                 return attr1?.Name == attr2?.Name &&
//                        attr1?.Value == attr2?.Value &&
//                        attr1?.Min == attr2?.Min &&
//                        attr1?.Max == attr2?.Max &&
//                        attr1?.Step == attr2?.Step &&
//                        attr1?.Mutable == attr2?.Mutable;
//             }
//
//             public int GetHashCode(Attribute attr)
//             {
//                 return attr.Name != null ? attr.Name.GetHashCode() : 0;
//             }
//         }
//     }
// }
