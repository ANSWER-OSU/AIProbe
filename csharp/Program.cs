using AIprobe.Models;
using AIprobe.Parsers;

namespace AIprobe
{
    internal class Program
    {
        static void Main(string[] args)
        {
            string filePath = @"C:\Users\rahil\Downloads\EnvConfig.xml";
            string ActionSpacefilePath = @"C:\Users\rahil\Downloads\actionspace.xml";

            EnvironmentParser enviromentParser = new EnvironmentParser(filePath);

            EnvironmentModel environment = enviromentParser.ParseEnvironment();

            ActionSpaceParser actionSpacPparser = new ActionSpaceParser(filePath);

            ActionSpaceModel actionSpace = actionSpacPparser.ParseActionSpace();

            if (actionSpace != null && environment != null) { 
            
            }


            //if (environment != null)
            //{
            //    // Print environment details
            //    Console.WriteLine($"Environment Name: {environment.Name}, Type: {environment.Type}");

            //    // Print agent details
            //    foreach (var agent in environment.Agents.AgentList)
            //    {
            //        Console.WriteLine($"Agent ID: {agent.Id}, Name: {agent.Name}, Type: {agent.Type}");
            //    }

            //    // Print object details
            //    foreach (var obj in environment.Objects.ObjectList)
            //    {
            //        Console.WriteLine($"Object ID: {obj.Id}, Name: {obj.Name}, Type: {obj.Type}");
            //    }

            //    // Print hazardous objects
            //    if (environment.EnvironmentFeatures?.Hazards?.HazardList != null)
            //    {
            //        foreach (var hazard in environment.EnvironmentFeatures.Hazards.HazardList)
            //        {
            //            Console.WriteLine($"Hazard ID: {hazard.Id}, Name: {hazard.Name}, Damage: {hazard.Damage}");
            //        }
            //    }

            //    // Print physical properties
            //    if (environment.EnvironmentFeatures?.PhysicalProperties?.Properties != null)
            //    {
            //        foreach (var property in environment.EnvironmentFeatures.PhysicalProperties.Properties)
            //        {
            //            Console.WriteLine($"Property Name: {property.Name}, Value: {property.Value}, Description: {property.Description}");
            //        }
            //    }
            //}
            //else
            //{
            //    Console.WriteLine("Failed to parse the environment XML.");
            //}
        }
    }
}
