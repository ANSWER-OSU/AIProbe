using System.Data;
using AIprobe.Models;
using Attribute = AIprobe.Models.Attribute;

namespace AIprobe.Preprocessing;

using Environment = AIprobe.Models.Environment;
public class AttributePreprocessor
{
    public void ProcessAttributes(Environment environment)
    {
        
        // Build a dictionary of attributes and their values
        var attributeValues = BuildAttributeDictionary(environment.Attributes);

        //Process Environmental Attributes
        Console.WriteLine("Processing Environmental Attributes...");
        foreach (var attribute in environment.Attributes)
        {
            ProcessAndReplacePlaceholders(attribute, attributeValues);
        }
        //
        // Process Agents
        Console.WriteLine("\nProcessing Agent Attributes...");
        foreach (var agent in environment.Agents.AgentList)
        {
            foreach (var attribute in agent.Attributes)
            {
                ProcessAndReplacePlaceholders(attribute, attributeValues);
            }
        }
        //
        // // Process Objects
        // Console.WriteLine("\nProcessing Object Attributes...");
        // foreach (var obj in environment.Objects.ObjectList)
        // {
        //     foreach (var attribute in obj.Attributes)
        //     {
        //         ProcessAndReplacePlaceholders(attribute, attributeValues);
        //     }
        // }
       Console.WriteLine(attributeValues);
        
       
    }

    private static Dictionary<string, int> BuildAttributeDictionary(List<Attribute> attributes)
    {
        var attributeValues = new Dictionary<string, int>();

        foreach (var attribute in attributes)
        {
            if (int.TryParse(attribute.Value.Content, out int value))
            {
                attributeValues[attribute.Name.Value] = value;
            }
        }

        return attributeValues;
    }

    private static void ProcessAndReplacePlaceholders(Attribute attribute, Dictionary<string, int> attributeValues)
    {
        // Replace placeholders in Min and Max
        attribute.Constraint.Max = EvaluateExpression(attribute.Constraint.Min, attributeValues);
        attribute.Constraint.Max = EvaluateExpression(attribute.Constraint.Max, attributeValues);
    
        // Log the updated Attribute details
        Console.WriteLine($"Processed Attribute: {attribute.Name.Value}");
        Console.WriteLine($"  Min: {attribute.Constraint.Min}, Max: {attribute.Constraint.Max}");
    }
    //
    private static string EvaluateExpression(string expression, Dictionary<string, int> attributeValues)
    {
        if (string.IsNullOrWhiteSpace(expression))
            return expression;
    
        try
        {
            // Replace attribute names in the expression with their values
            foreach (var kvp in attributeValues)
            {
                expression = expression.Replace(kvp.Key, kvp.Value.ToString());
            }
    
            // Evaluate the expression using DataTable's Compute method
            var result = new DataTable().Compute(expression, null);
            return result.ToString();
        }
        catch
        {
            Console.WriteLine($"Error evaluating expression: {expression}");
            return expression; // Return original expression if evaluation fails
        }
    }
}
