using AIprobe.Logging;
using AIprobe.Models;
using Environment = AIprobe.Models.Environment;

namespace AIprobe.TaskGenerator
{
    public class EnvTaskGenerator
    {
        // private Random random;
        //
        // // Constructor with seed parameter
        // public EnvTaskGenerator(int seed)
        // {
        //     random = new Random(seed); 
        // }
        //
        // /// <summary>
        // /// Generate various tasks based on the environment within the given time
        // /// </summary>
        // /// <param name="environmentConfig">environment config object</param>
        // /// <param name="timeLimitInSeconds">time</param>
        // /// <returns></returns>
        // public List<(AIprobe.Models.Environment,Environment)> GenerateTasks(Environment environmentConfig,
        //     int timeLimitInSeconds)
        // {
        //     Console.WriteLine(random.Next()); 
        //     
        //     
        //     List<(AIprobe.Models.Environment,Environment)> tasks = new List<(AIprobe.Models.Environment,Environment)>();
        //     DateTime startTime = DateTime.Now;
        //
        //     Logger.LogInfo($"Task generation started with a time limit of {timeLimitInSeconds} seconds.");
        //     var totalMutableAttributes = 0;
        //     int taskCount = 0;
        //     while ((DateTime.Now - startTime).TotalSeconds < timeLimitInSeconds)
        //     {
        //         AIprobe.Models.Environment initialState = Program.DeepCopy(environmentConfig);
        //         //AIprobe.Models.Environment finalState = Program.DeepCopy(environmentConfig);
        //         
        //         // gentrating new initial state
        //         MutateAgentProperties(initialState);
        //         MutateObjectProperties((initialState));
        //
        //         AIprobe.Models.Environment finalState = Program.DeepCopy(initialState);
        //         MutateAgentProperties(finalState);
        //         //MutateObjectProperties((finalState));
        //         tasks.Add((initialState, finalState));
        //     }
        //
        //     Logger.LogInfo(
        //         $"Task generation completed. {tasks.Count} tasks were generated within {timeLimitInSeconds} seconds.");
        //     return tasks;
        // }
        //
        //
        // /// <summary>
        // /// This method processes the mutable properties of agents within the environment.
        // /// It selects random mutable attributes and modifies them accordingly.
        // /// </summary>
        // /// <param name="environmentConfig"></param>
        // /// <returns></returns>
        // private Environment MutateAgentProperties(Environment environmentConfig){
        //     var mutableAttributes = ProcessAgentListForMutableAttributes(environmentConfig.Agents.AgentList);
        //     
        //     Dictionary<string, List<string>> selectedAttributess = RandomlySelectValuesFromDictionary(mutableAttributes);
        //     
        //     ModifyMutableAttributes(environmentConfig.Agents.AgentList, mutableAttributes);
        //
        //     return environmentConfig;
        //     
        // }
        //
        // /// <summary>
        // /// Processes a list of agents and identifies mutable attributes.
        // /// </summary>
        // /// <param name="agentList">The list of agents to process.</param>
        // /// <returns>
        // /// A dictionary where the key is the agent's ID , and the value is a list of mutable attribute names for that agent.
        // /// </returns>
        // private Dictionary<string, List<string>> ProcessAgentListForMutableAttributes(List<AIprobe.Models.Agent> agentList)
        // {
        //     Dictionary<string, List<string>> agentMutableAttributes = new Dictionary<string, List<string>>();
        //
        //     foreach (var agent in agentList)
        //     {
        //         List<string> mutableAttributeNames = new List<string>();
        //
        //         // Process Position attributes
        //         foreach (var attr in agent.Position.Attributes)
        //         {
        //             if (attr.Mutable?.Value == true)
        //             {
        //                 mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
        //             }
        //         }
        //
        //         // Process Direction attributes
        //         foreach (var attr in agent.Direction.Attributes)
        //         {
        //             if (attr.Mutable?.Value == true)
        //             {
        //                 mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
        //             }
        //         }
        //
        //         // If there are mutable attributes, add them to the dictionary with the agent's ID
        //         if (mutableAttributeNames.Count > 0)
        //         {
        //             agentMutableAttributes[agent.Id.ToString()] = mutableAttributeNames;
        //         }
        //     }
        //
        //     return agentMutableAttributes; // Return the dictionary with agent ID and mutable attribute names
        // }
        //
        // /// <summary>
        // /// Randomly selects a subset of values from each key's list in the provided dictionary. 
        // /// </summary>
        // /// <param name="attributesDictionary">
        // /// A dictionary where the key is eithe agent id or object id  and the value  is a list of mutable attribute names associated with that entity.
        // /// </param>
        // /// <returns>
        // /// A dictionary where the key is eithe agent id or object id  and the value is a random list of mutable attribute names associated with that entity.
        // /// </returns>
        // private Dictionary<string, List<string>> RandomlySelectValuesFromDictionary(Dictionary<string, List<string>> attributesDictionary)
        // {
        //     Random random = new Random();
        //     Dictionary<string, List<string>> selectedValuesDictionary = new Dictionary<string, List<string>>();
        //
        //     // Iterate over each key in the dictionary
        //     foreach (var entry in attributesDictionary)
        //     {
        //         string key = entry.Key;  // The key (Agent or Object ID)
        //         List<string> values = entry.Value;  // The list of mutable attribute names for this key
        //
        //         if (values.Count == 0)
        //         {
        //             // If there are no values for this key, skip
        //             continue;
        //         }
        //
        //         // Randomly decide how many values to select for this key (between 1 and the total number of values)
        //         int numberToSelect = random.Next(1, values.Count + 1);
        //
        //         List<string> selectedValues = new List<string>();
        //
        //         // Randomly select unique values
        //         while (selectedValues.Count < numberToSelect)
        //         {
        //             int index = random.Next(0, values.Count);  // Random index
        //             string selectedValue = values[index];
        //
        //             if (!selectedValues.Contains(selectedValue))  // Ensure no duplicates
        //             {
        //                 selectedValues.Add(selectedValue);
        //             }
        //         }
        //
        //         // Add the selected values to the result dictionary
        //         selectedValuesDictionary[key] = selectedValues;
        //     }
        //
        //     return selectedValuesDictionary;
        // }
        //
        //
        // /// <summary>
        // /// Modifies the mutable attributes for a list of agents based on the provided dictionary of mutable attributes.
        // /// </summary>
        // /// <param name="agentList">The list of agents to process for mutable attributes.</param>
        // /// <param name="mutableAttributes">
        // /// A dictionary where the key is the agent's id, and the value is a list of mutable attribute names that should be modified for that agent.
        // /// </param>
        // private void ModifyMutableAttributes(List<AIprobe.Models.Agent> agentList, Dictionary<string, List<string>> mutableAttributes)
        // {
        //     foreach (var agent in agentList)
        //     {
        //         if (mutableAttributes.ContainsKey(agent.Id.ToString()))
        //         {
        //             // Get the mutable attribute names for this agent
        //             List<string> attributesToMutate = mutableAttributes[agent.Id.ToString()];
        //
        //             // Modify Position attributes and store the selected values
        //             ModifyEntityAttributes(agent.Position.Attributes, attributesToMutate);
        //
        //             // Modify Direction attributes and store the selected values
        //             ModifyEntityAttributes(agent.Direction.Attributes, attributesToMutate);
        //         }
        //     }
        // }
        //
        //
        // /// <summary>
        // /// This method processes the mutable properties of objects within the environment.
        // /// It selects random mutable attributes and modifies them accordingly.
        // /// </summary>
        // /// <param name="environmentConfig"></param>
        // /// <returns></returns>
        // private Environment MutateObjectProperties(Environment environmentConfig){
        //     var mutableAttributes = ProcessObjectListForMutableAttributes(environmentConfig.Objects.ObjectList);
        //         
        //     // Randomly select indices from mutable attributes
        //     Dictionary<string, List<string>> selectedAttributess = RandomlySelectValuesFromDictionary(mutableAttributes);
        //     
        //     ModifyMutableAttributes(environmentConfig.Objects.ObjectList, mutableAttributes);
        //
        //     return environmentConfig;
        //     
        // }
        //
        //
        // /// <summary>
        // /// process object list and gather mutable attribute names
        // /// </summary>
        // /// <param name="objectList"></param>
        // /// <returns></returns>
        // private Dictionary<string, List<string>> ProcessObjectListForMutableAttributes(List<AIprobe.Models.Object> objectList)
        // {
        //     Dictionary<string, List<string>> objectMutableAttributes = new Dictionary<string, List<string>>();
        //
        //     foreach (var obj in objectList)
        //     {
        //         List<string> mutableAttributeNames = new List<string>();
        //
        //         // if (obj.Type != "interactive")
        //         // {
        //         //      continue;
        //         // }
        //         
        //         // Process Object attributes
        //         foreach (var attr in obj.ObjectAttributes.Attributes)
        //         {
        //             if (attr.Mutable?.Value == true)
        //             {
        //                 mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
        //             }
        //         }
        //
        //         foreach (var attr in obj.Position.Attributes)
        //         {
        //             if (attr.Mutable?.Value == true)
        //             {
        //                 mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
        //             }
        //         }
        //
        //         // If there are mutable attributes, add them to the dictionary with the object's ID
        //         if (mutableAttributeNames.Count > 0)
        //         {
        //             objectMutableAttributes[obj.Id.ToString()] = mutableAttributeNames;
        //         }
        //     }
        //
        //     return objectMutableAttributes; // Return the dictionary with object ID and mutable attribute names
        // }
        //
        //
        // /// <summary>
        // /// Modify mutable attributes for Objects,based on the dictionary of mutable attributes
        // /// </summary>
        // /// <param name="objectList"></param>
        // /// <param name="mutableAttributes"></param>
        // private void ModifyMutableAttributes(List<AIprobe.Models.Object> objectList, Dictionary<string, List<string>> mutableAttributes)
        // {
        //     foreach (var obj in objectList)
        //     {
        //         if (mutableAttributes.ContainsKey(obj.Id.ToString()))
        //         {
        //             // Get the mutable attribute names for this object
        //             List<string> attributesToMutate = mutableAttributes[obj.Id.ToString()];
        //             
        //             ModifyEntityAttributes(obj.Position.Attributes, attributesToMutate);
        //
        //             // Modify Object attributes and store the selected values
        //             ModifyEntityAttributes(obj.ObjectAttributes.Attributes, attributesToMutate);
        //         }
        //     }
        // }
        //
        //
        // /// <summary>
        // /// to modify entity attributes (used by both Agent and Object) and store selected values
        // /// </summary>
        // /// <param name="attributes"></param>
        // /// <param name="attributesToMutate"></param>
        // private void ModifyEntityAttributes(List<AIprobe.Models.Attribute> attributes, List<string> attributesToMutate)
        // {
        //     foreach (var attr in attributes)
        //     {
        //         // Check if this attribute's name is in the list of names to mutate
        //         if (attributesToMutate.Contains(attr.Name.Value))
        //         {
        //             // Apply changes to the attribute
        //             var newValue = ChangeAttributeValue(attr); // Example of modifying the attribute value
        //     
        //             // Assign the mutated value back to the attribute
        //             attr.Value.ValueData = newValue.ToString();
        //         }
        //     }
        // }
        //
        //
        // /// <summary>
        // /// Randomly change the value of the attribute based on the data type
        // /// </summary>
        // /// <param name="attr">atributes of the agent or object</param>
        // /// <returns>Modified value of the attribute</returns>
        // private object ChangeAttributeValue(AIprobe.Models.Attribute attr)
        // {
        //     Random random = new Random();
        //
        //     // Change the value based on the data type
        //     if (attr.DataType.Value == "int")
        //     {
        //      
        //         
        //         // Example: Random integer value between Min and Max
        //         return random.Next(Convert.ToInt32(attr.Min.Value), Convert.ToInt32(attr.Max.Value));
        //     }
        //     else if (attr.DataType.Value == "float")
        //     {
        //         // Example: Random float value between Min and Max
        //         return (float)(random.NextDouble() * (Convert.ToSingle(attr.Max.Value) - Convert.ToSingle(attr.Min.Value)) + Convert.ToSingle(attr.Min.Value));
        //     }
        //     else if (attr.DataType.Value == "string")
        //     {
        //         // If it's a string, randomly select from the ValueList
        //         if (attr.ValueList != null && attr.ValueList.Pairs != null && attr.ValueList.Pairs.Count > 0)
        //         {
        //             // Randomly select a Pair from the ValueList
        //             int randomIndex = random.Next(0, attr.ValueList.Pairs.Count);
        //             return attr.ValueList.Pairs[randomIndex].Value; // Return the value from the selected pair
        //         }
        //     }
        //     else if (attr.DataType.Value == "bool")
        //     {
        //         // Randomly assign true or false for boolean type
        //         return random.Next(0, 2) == 0; // 50% chance of true or false
        //     }
        //
        //     // Default: return the original value if no change is needed
        //     return attr.Value.ValueData;
        // }
        //

    }
}
