using System;
using System.Collections.Generic;

namespace AIprobe.Models
{
    public class EnvironmentComparer
    {
        // /// <summary>
        // /// Compare two Environment objects and return a list of differences.
        // /// </summary>
        // /// <param name="env1">First environment</param>
        // /// <param name="env2">Second environment</param>
        // /// <returns>List of differences as strings</returns>
        // public static List<string> CompareEnvironments(Environment env1, Environment env2)
        // {
        //     List<string> differences = new List<string>();
        //
        //     // Compare Name
        //     if (env1.Name != env2.Name)
        //     {
        //         differences.Add($"Name differs: {env1.Name} vs {env2.Name}");
        //     }
        //
        //     // Compare Type
        //     if (env1.Type != env2.Type)
        //     {
        //         differences.Add($"Type differs: {env1.Type} vs {env2.Type}");
        //     }
        //
        //     // Compare Agents
        //     if (!env1.Agents.Equals(env2.Agents))
        //     {
        //         differences.Add("Agents differ.");
        //         CompareAgents(env1.Agents, env2.Agents, differences);
        //     }
        //
        //     // Compare Objects (if objects exist)
        //     if (!env1.Objects.Equals(env2.Objects))
        //     {
        //         differences.Add("Objects differ.");
        //         CompareObjects(env1.Objects, env2.Objects, differences);
        //     }
        //
        //     // Compare Environmental Properties (if properties exist)
        //     if (!env1.EnvironmentalProperties.Equals(env2.EnvironmentalProperties))
        //     {
        //         differences.Add("Environmental Properties differ.");
        //         //CompareEnvironmentalProperties(env1.EnvironmentalProperties, env2.EnvironmentalProperties, differences);
        //     }
        //
        //     return differences;
        // }
        //
        // private static void CompareAgents(Agents agents1, Agents agents2, List<string> differences)
        // {
        //     if (agents1.AgentList.Count != agents2.AgentList.Count)
        //     {
        //         differences.Add($"Agent count differs: {agents1.AgentList.Count} vs {agents2.AgentList.Count}");
        //         return;
        //     }
        //
        //     for (int i = 0; i < agents1.AgentList.Count; i++)
        //     {
        //         var agent1 = agents1.AgentList[i];
        //         var agent2 = agents2.AgentList[i];
        //
        //         if (agent1.Id != agent2.Id)
        //         {
        //             differences.Add($"Agent ID differs at index {i}: {agent1.Id} vs {agent2.Id}");
        //         }
        //
        //         if (agent1.Name != agent2.Name)
        //         {
        //             differences.Add($"Agent Name differs at index {i}: {agent1.Name} vs {agent2.Name}");
        //         }
        //
        //         if (agent1.Type != agent2.Type)
        //         {
        //             differences.Add($"Agent Type differs at index {i}: {agent1.Type} vs {agent2.Type}");
        //         }
        //
        //         if (!ComparePositions(agent1.Position, agent2.Position, i, differences))
        //         {
        //             differences.Add($"Agent Position differs at index {i}");
        //         }
        //
        //         if (!CompareDirections(agent1.Direction, agent2.Direction, i, differences))
        //         {
        //             differences.Add($"Agent Direction differs at index {i}");
        //         }
        //     }
        // }
        //
        // private static bool ComparePositions(Position pos1, Position pos2, int agentIndex, List<string> differences)
        // {
        //     if (pos1.Attributes.Count != pos2.Attributes.Count)
        //     {
        //         differences.Add(
        //             $"Agent {agentIndex} Position attribute count differs: {pos1.Attributes.Count} vs {pos2.Attributes.Count}");
        //         return false;
        //     }
        //
        //     for (int i = 0; i < pos1.Attributes.Count; i++)
        //     {
        //         var attr1 = pos1.Attributes[i];
        //         var attr2 = pos2.Attributes[i];
        //
        //         if (!attr1.Equals(attr2))
        //         {
        //             differences.Add(
        //                 $"Agent {agentIndex} Position Attribute {i} differs: {attr1.Name.Value} vs {attr2.Name.Value}");
        //             return false;
        //         }
        //     }
        //
        //     return true;
        // }
        //
        // private static bool CompareDirections(Direction dir1, Direction dir2, int agentIndex, List<string> differences)
        // {
        //     if (dir1.Attributes.Count != dir2.Attributes.Count)
        //     {
        //         differences.Add(
        //             $"Agent {agentIndex} Direction attribute count differs: {dir1.Attributes.Count} vs {dir2.Attributes.Count}");
        //         return false;
        //     }
        //
        //     for (int i = 0; i < dir1.Attributes.Count; i++)
        //     {
        //         var attr1 = dir1.Attributes[i];
        //         var attr2 = dir2.Attributes[i];
        //
        //         if (!attr1.Equals(attr2))
        //         {
        //             differences.Add(
        //                 $"Agent {agentIndex} Direction Attribute {i} differs: {attr1.Name.Value} vs {attr2.Name.Value}");
        //             return false;
        //         }
        //     }
        //
        //     return true;
        // }
        //
        // private static void CompareObjects(Objects objects1, Objects objects2, List<string> differences)
        // {
        //     if (objects1.ObjectList.Count != objects2.ObjectList.Count)
        //     {
        //         differences.Add($"Object count differs: {objects1.ObjectList.Count} vs {objects2.ObjectList.Count}");
        //         return;
        //     }
        //
        //     for (int i = 0; i < objects1.ObjectList.Count; i++)
        //     {
        //         var object1 = objects1.ObjectList[i];
        //         var object2 = objects2.ObjectList[i];
        //
        //         if (object1.Id != object2.Id)
        //         {
        //             differences.Add($"Object ID differs at index {i}: {object1.Id} vs {object2.Id}");
        //         }
        //
        //         if (object1.Name != object2.Name)
        //         {
        //             differences.Add($"Object Name differs at index {i}: {object1.Name} vs {object2.Name}");
        //         }
        //
        //         if (!object1.Position.Equals(object2.Position))
        //         {
        //             differences.Add($"Object Position differs at index {i}");
        //         }
        //
        //         if (!object1.ObjectAttributes.Equals(object2.ObjectAttributes))
        //         {
        //             differences.Add($"Object Attributes differ at index {i}");
        //         }
        //     }
        // }

        //     private static void CompareEnvironmentalProperties(EnvironmentalProperties properties1, EnvironmentalProperties properties2, List<string> differences)
        //     {
        //         if (properties1.Properties.Count != properties2.Properties.Count)
        //         {
        //             differences.Add($"Environmental Property count differs: {properties1.Properties.Count} vs {properties2.Properties.Count}");
        //             return;
        //         }
        //
        //         for (int i = 0; i < properties1.Properties.Count; i++)
        //         {
        //             var prop1 = properties1.Properties[i];
        //             var prop2 = properties2.Properties[i];
        //
        //             if (prop1.Name != prop2.Name)
        //             {
        //                 differences.Add($"Property Name differs at index {i}: {prop1.Name} vs {prop2.Name}");
        //             }
        //             if (prop1.Value != prop2.Value)
        //             {
        //                 differences.Add($"Property Value differs at index {i}: {prop1.Value} vs {prop2.Value}");
        //             }
        //         }
        //     }
        // }
    }
}
