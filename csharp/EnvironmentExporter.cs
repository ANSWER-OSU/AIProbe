using System.Text;

namespace AIprobe;
using Environment = AIprobe.Models.Environment;

public class EnvironmentExporter
{
    
    public static void SaveEnvironmentsToCsv(List<Environment> environments, string filePath)
    {
        using (var writer = new StreamWriter(filePath))
        {
            // Write header row
            foreach (var environment in environments)
            {
                // Flatten environment into rows
                var rows = FlattenEnvironment(environment);
                writer.WriteLine(rows);
                
            }
        }
    }

    private static string FlattenEnvironment(Environment environment)
    {
        var rows = new List<string>();

        StringBuilder sb = new StringBuilder();
        foreach (var attribute in environment.Attributes)
        {
           Console.WriteLine(attribute.Value.Content);
           sb.Append(attribute.Value.Content);
           sb.Append(',');
        }

        foreach (var agent in environment.Agents.AgentList)
        {
            foreach (var agentvalue in agent.Attributes)
            {
                Console.WriteLine(agentvalue.Value.Content);
                sb.Append(agentvalue.Value.Content);
                sb.Append(',');
            }
        }

        foreach (var objects in environment.Objects.ObjectList)
        {
            foreach (var objectsAttribute in objects.Attributes)
            {
                Console.WriteLine(objectsAttribute.Value.Content);
                sb.Append(objectsAttribute.Value.Content);
                sb.Append(',');
                
            }
        }
        
        Console.WriteLine(sb.ToString());
        
        // Flatten global attributes
        //string globalAttributes = FlattenAttributes(environment.Attributes);

        // Flatten agents
       

        return sb.ToString();
    }
    
    
}