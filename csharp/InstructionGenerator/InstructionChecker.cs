using System.Net.Mail;
using AIprobe.Logging;
using AIprobe.Models;
using AIprobe.Parsers;
using Microsoft.VisualBasic;
using Environment = AIprobe.Models.Environment;

using StackExchange.Redis;
using System.Text.Json;
namespace AIprobe.InstructionGenerator;

public class InstructionChecker
{
    /// <summary>
    /// Check the is any instruction which can be applied to env so initial state changes tot desied final state.
    /// </summary>
    /// <param name="initialEnvironmentState">object of initial environment</param>
    /// <param name="finalEnvironmentState">object of mutated environment</param>
    /// <param name="timeLimitInSeconds">max time to genrate and check is instruction exists which statisfy tha task</param>
    /// <returns>result in form od [arrayOfInstrction[],bool value]</returns>
    public List<object[]> InstructionExists(Environment initialEnvironmentState, ActionSpace actionSpace, int timeLimitInSeconds,string initialStateHashValue,string finalStateHashValue,out bool instructionExists)
    {
        instructionExists = false;
        List<object[]> results = new List<object[]>();
        
        Logger.LogInfo("Starting instruction validation.");
        

        // Dictionary to track instriction that led to each environment state
        Dictionary<string, List<string>> instructionStateDictionary = new Dictionary<string, List<string>>();

        // Dictionary to track remaining actions for each environment state
       // Dictionary<AIprobe.Models.Environment, List<string>> completedActionsDictionary =
        Dictionary<string, List<string>> completedActionsDictionary =  new Dictionary<string, List<string>>();
        
        // Queue for BFS traversal of environment states
        Queue<Environment> environmentQueue = new Queue<AIprobe.Models.Environment>();
        
        environmentQueue.Enqueue(initialEnvironmentState);
        DateTime startTime = DateTime.Now;
        CancellationTokenSource cts = new CancellationTokenSource();
        cts.CancelAfter(TimeSpan.FromSeconds(timeLimitInSeconds));
        while (environmentQueue.Count > 0)
        {
            cts.Token.ThrowIfCancellationRequested();
            try
            {


                // Dequeue the current environment state to explore
                var currentEnvironment = environmentQueue.Dequeue();

                string currentEnviromentHashValues = HashGenerator.ComputeEnvironmentHash(currentEnvironment);

                if (currentEnviromentHashValues.Equals(finalStateHashValue))
                {

                    // Get the list of actions that led to this environment state
                    if (instructionStateDictionary.TryGetValue(finalStateHashValue, out List<string> instructionSet))
                    {
                        results.Add(new object[] { string.Join(", ", instructionSet), "Safe" });
                        instructionExists = true;

                        Aiprobe.LogAndDisplay("####Found instruction set###");
                        return results;
                    }

                    Aiprobe.LogAndDisplay("Found final state but could not found final instructions sets###");
                    return results;
                }


                // Retrieve remaining actions for this state
                List<string> remainingActions = new List<string>();

                remainingActions = AddEnvironmentAndCheckActions(currentEnviromentHashValues, actionSpace,
                    completedActionsDictionary);


                foreach (string action in new List<string>(remainingActions))
                {
                    string filePath = Aiprobe.envConfigFile;

                    bool safeCondition = true;
                    Environment updatedEnvironment = new Environment();
                    try
                    {
                        // updatedEnvironment =
                        // runner.RunPythonScript( tempFuzzerFilePath,wraperFilePath, action, out safeCondition);
                        updatedEnvironment = CallPythonWrapperWithRedis(currentEnvironment, action, out safeCondition);

                    }
                    catch (Exception e)
                    {

                        Aiprobe.LogAndDisplay(e.Message);
                        return results;

                    }
                    // Run the Python script to get the updated environment statE

                    //

                    string updatedEnviromentHashValue = HashGenerator.ComputeEnvironmentHash(updatedEnvironment);

                    if (updatedEnviromentHashValue.Equals(finalStateHashValue))
                    {
                        if (safeCondition)
                        {
                            Aiprobe.LogAndDisplay("####Found instruction set###");

                            if (instructionStateDictionary.TryGetValue(currentEnviromentHashValues,
                                    out List<string> instructionSet))
                            {
                                instructionExists = true;
                                instructionSet.Add(action);
                                results.Add(new object[] { string.Join(", ", instructionSet), "Safe" });
                                Aiprobe.LogAndDisplay(
                                    $"Stopping instruction validation. instruction found:{instructionExists}");
                                return results;
                            }
                        }
                    }

                    //bool createdNewKey = instructionStateDictionary.TryAdd(updatedEnviromentHashValue, new List<string>());



                    bool createdNewActionKey =
                        completedActionsDictionary.TryAdd(updatedEnviromentHashValue, new List<string>());


                    List<string> newInstructionSet = new List<string>();

                    if (instructionStateDictionary.TryAdd(updatedEnviromentHashValue, new List<string>()))
                    {

                        Aiprobe.totalEnviroementState++;

                        if (instructionStateDictionary.TryGetValue(currentEnviromentHashValues,
                                out List<string> previousInstructionSet))
                            if (previousInstructionSet.Count > 0)
                            {
                                foreach (var VARIABLE in previousInstructionSet)
                                {
                                    newInstructionSet.Add(VARIABLE);
                                }
                            }


                        if (safeCondition == false)
                        {
                            newInstructionSet.Add(action);
                            instructionStateDictionary[updatedEnviromentHashValue] = newInstructionSet;
                            results.Add(new object[] { string.Join(", ", newInstructionSet), "Unsafe" });
                            double keyCount = Aiprobe.unsafeStatePosition.Count();
                            keyCount++;
                            Aiprobe.unsafeStatePosition[keyCount] = Aiprobe.totalEnviroementState;

                        }
                        else
                        {
                            newInstructionSet.Add(action);
                            instructionStateDictionary[updatedEnviromentHashValue] = newInstructionSet;
                            //newInstructionSet.Add(action);
                            environmentQueue.Enqueue(updatedEnvironment);
                        }

                    }

                }
            }
            catch (OperationCanceledException)
            {
                Aiprobe.LogAndDisplay("The instruction generation was canceled due to a timeout.");
                Aiprobe.LogAndDisplay($"Stopping instruction validation. instruction found:{instructionExists}");
                cts.Dispose();
                return results;
            }

        }
        Aiprobe.LogAndDisplay($"Stopping instruction validation. instruction found:{instructionExists}");
        return results;
    }

    private List<string> AddEnvironmentAndCheckActions(string hashValue, ActionSpace actionSpace, Dictionary<string, List<string>> actionDictionary)
    {
        List<string> remainingActions;

        // Check if the environment already exists in the dictionary
        if (actionDictionary.TryGetValue(hashValue, out remainingActions))
        {
            if (remainingActions == null|| remainingActions.Count==0)  
            {
                remainingActions = new List<string>();
                foreach (var action in actionSpace.Actions.ActionList)
                {
                    remainingActions.Add(action.Name);
                }

                return remainingActions;
            }

            // Check if the number of actions matches
            if (remainingActions.Count == actionSpace.Actions.ActionList.Count)
            {
                Aiprobe.LogAndDisplay("Environment already exists in the dictionary. Returning empty list.");
                return new List<string>(); // Return an empty list
            }
        }
        else
        {
            // If the environment doesn't exist, initialize remainingActions and add it to the dictionary
            remainingActions = new List<string>();
            foreach (var action in actionSpace.Actions.ActionList)
            {
                remainingActions.Add(action.Name);
            }
        
            // Add the environment and its actions to the dictionary
            actionDictionary[hashValue] = remainingActions;
        
            Console.WriteLine("New environment added to the dictionary with its actions.");
            return remainingActions;
        }

        return remainingActions;
    }

   
    
    
    
    

    private Environment CallPythonWrapperWithRedis(
        Environment environment,
        string action,
        out bool safeCondition)
    {
        safeCondition = false;

        // Connect to Redis
        var redis = ConnectionMultiplexer.Connect("localhost");
        var db = redis.GetDatabase();

        // Prepare data to send to Python
        var payload = new
        {
            Environment = environment, // Serialize the environment object
            Action = action
        };

        // Serialize and push data to Redis
        string payloadKey = "environment:payload";
        string resultKey = "environment:result";
        db.StringSet(payloadKey, JsonSerializer.Serialize(payload));

        // Wait for Python to process and return the result
        while (true)
        {
            if (db.KeyExists(resultKey))
            {
                // Retrieve and deserialize the result
                var resultJson = db.StringGet(resultKey);
                var result = JsonSerializer.Deserialize<Result>(resultJson);

                // Clean up Redis keys
                db.KeyDelete(payloadKey);
                db.KeyDelete(resultKey);

                // Extract result data
                safeCondition = result.SafeCondition;
                return result.UpdatedEnvironment;
            }

            // Small delay to prevent excessive polling
            Thread.Sleep(100);
        }
    }
    

// Helper class for deserializing Python's response
    private class Result
    {
        public Environment UpdatedEnvironment { get; set; }
        public bool SafeCondition { get; set; }
    }
    
    
    
    
}