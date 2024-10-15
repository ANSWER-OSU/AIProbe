using System.Net.Mail;
using AIprobe.Logging;
using AIprobe.Models;

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
    public List<object[]>  InstructionExists(AIprobe.Models.Environment initialEnvironmentState, AIprobe.Models.Environment finalEnvironmentState,ActionSpace actionSpace, int timeLimitInSeconds)
    {
        List<object[]> results = new List<object[]>();
        
        
        // for testing purpose 
        // var finalAgent = finalEnvironmentState.Agents.AgentList.FirstOrDefault();
        // if (finalAgent != null)
        // {
        //     finalAgent.Position.Attributes[0].Value.ValueData = "1";
        //     finalAgent.Position.Attributes[1].Value.ValueData= "2";
        // }
        
        Logger.LogInfo("Starting instruction validation.");
        
        // Dictionary to track instriction that led to each environment state
        Dictionary<AIprobe.Models.Environment, List<string>> instructionStateDictionary = new Dictionary<AIprobe.Models.Environment, List<string>>();
        
        // Dictionary to track remaining actions for each environment state
        Dictionary<AIprobe.Models.Environment, List<string>> remainingActionsDictionary = new Dictionary<AIprobe.Models.Environment, List<string>>();

        // Queue for BFS traversal of environment states
        Queue<AIprobe.Models.Environment> environmentQueue = new Queue<AIprobe.Models.Environment>();

        // Initialize the starting state and its actions
        instructionStateDictionary.Add(initialEnvironmentState, new List<string>());
        environmentQueue.Enqueue(initialEnvironmentState);
        
        DateTime startTime = DateTime.Now;

        while (environmentQueue.Count > 0 && (DateTime.Now - startTime).TotalSeconds < timeLimitInSeconds)
        {
            // Dequeue the current environment state to explore
            AIprobe.Models.Environment currentEnvironment = environmentQueue.Dequeue();

            if (currentEnvironment.Equals(finalEnvironmentState))
            {
                // Get the list of actions that led to this environment state
                List<string> instructionSet = instructionStateDictionary[currentEnvironment];
                results.Add(new object[] { string.Join(", ", instructionSet), "yes" });
                return results;
            }
            
            // Retrieve remaining actions for this state
            List<string> remainingActions;
            if (!remainingActionsDictionary.TryGetValue(currentEnvironment, out remainingActions))
            {
                remainingActions = GetRemaingActions(currentEnvironment, actionSpace, remainingActionsDictionary);
                remainingActionsDictionary[currentEnvironment] = remainingActions;
            }
            
            //List<string> actionRemaing=  GetRemaingActions(currentEnvironment, actionSpace, remainingActionsDictionary);
            
            List<string> actionsToRemove = new List<string>();
            PythonRunner runner = new PythonRunner();
            
            foreach (string action in new List<string>(remainingActions))
            { 
                string filePath = Program.envConfigFile;
                
                // Run the Python script to get the updated environment state
                AIprobe.Models.Environment updatedEnvironment = runner.RunPythonScript(currentEnvironment, filePath,action,out bool safeCondition);
                
                var updatedAgent = updatedEnvironment.Agents.AgentList.FirstOrDefault();
                var finalAgentd = finalEnvironmentState.Agents.AgentList.FirstOrDefault();
                
                if (updatedEnvironment.Equals(finalEnvironmentState))
                {
                    Console.WriteLine("found");
                    List<string> instructionSet = new List<string>(instructionStateDictionary[currentEnvironment]);
                    instructionSet.Add(action);
                    results.Add(new object[] { string.Join(", ", instructionSet), "yes" });
                    return results;
                }

                // If the updated environment state hasn't been visited, add it to the queue and dictionary
                if (!instructionStateDictionary.ContainsKey(updatedEnvironment))
                {
                    List<string> newInstructionSet = new List<string>(instructionStateDictionary[currentEnvironment]);
                    newInstructionSet.Add(action);
                    instructionStateDictionary.Add(updatedEnvironment, newInstructionSet);
                    environmentQueue.Enqueue(updatedEnvironment);
                }
                
                if (safeCondition == false)
                {
                    List<string> instructionSet = instructionStateDictionary[currentEnvironment];
                    results.Add(new object[] { string.Join(", ", instructionSet), "no" }); 
                }
                
                
                // Update the remaining actions dictionary by removing the processed actions
                if (remainingActionsDictionary.ContainsKey(currentEnvironment))
                {
                    remainingActionsDictionary[currentEnvironment].Remove(action);
                }
                
            }
            
            results.Add(new object[] { currentEnvironment });
            return results;
        }
        
        Logger.LogInfo("Stopping instruction validation.");
        return results; 
    }
    
    private List<string> GetRemaingActions(AIprobe.Models.Environment currentEnvironmentState, ActionSpace actionSpace,
        Dictionary<AIprobe.Models.Environment, List<string>> actionDictionary)
    {
        List<string> remainingActions = new List<string>();
        
        if (actionDictionary.ContainsKey(currentEnvironmentState))
        {
            
            List<string> performedActions = actionDictionary[currentEnvironmentState];
            
            foreach (var action in actionSpace.Actions.ActionList)
            {
                // Check if the action name is not in the performed actions list
                bool actionPerformed = false;

                // Compare each action's name with the performed actions
                foreach (var performedAction in performedActions)
                {
                    if (action.Name == performedAction.ToString()) // Assuming performedActions stores action names as strings
                    {
                        actionPerformed = true;
                        break; // If the action is found in performed actions, stop checking further
                    }
                }

                // If the action was not performed, add it to the remaining actions list
                if (!actionPerformed)
                {
                    remainingActions.Add(action.Name);
                }
            }
        }
        else
        {
            // If the current state is not in the actionDictionary, return all actions from ActionSpace
            foreach (var action in actionSpace.Actions.ActionList)
            {
                remainingActions.Add(action.Name); // Add all action names
            }
        }
        
        
        return remainingActions; 
        
        
    }
}