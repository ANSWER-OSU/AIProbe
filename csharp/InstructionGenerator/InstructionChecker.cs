using System.Net.Mail;
using AIprobe.Logging;
using AIprobe.Models;
using AIprobe.Parsers;
using Microsoft.VisualBasic;
using Environment = AIprobe.Models.Environment;

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
    public List<object[]> InstructionExists(AIprobe.Models.Environment initialEnvironmentState,
        AIprobe.Models.Environment finalEnvironmentState, ActionSpace actionSpace, int timeLimitInSeconds,string initialStateHashValue,string finalStateHashValue)
    {
        List<object[]> results = new List<object[]>();
        
        Logger.LogInfo("Starting instruction validation.");

        // Dictionary to track instriction that led to each environment state
        Dictionary<string, List<string>> instructionStateDictionary =
            new Dictionary<string, List<string>>();

        // Dictionary to track remaining actions for each environment state
       // Dictionary<AIprobe.Models.Environment, List<string>> completedActionsDictionary =
        Dictionary<string, List<string>> completedActionsDictionary =
            new Dictionary<string, List<string>>();
        
        // Queue for BFS traversal of environment states
        Queue<AIprobe.Models.Environment> environmentQueue = new Queue<AIprobe.Models.Environment>();
        
        environmentQueue.Enqueue(initialEnvironmentState);
        DateTime startTime = DateTime.Now;

        int counter = 0;
        while (environmentQueue.Count > 0 && (DateTime.Now - startTime).TotalSeconds < timeLimitInSeconds)
        {
            // Dequeue the current environment state to explore
            var currentEnvironment = environmentQueue.Dequeue();
            
            EnvironmentParser parser = new EnvironmentParser("/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/TEMPLavaEnv.xml");
            parser.WriteEnvironment(currentEnvironment,out string currentEnviromentHashValues);
            
            // Environment secoundIntialEnv = new Environment();
            // // if (counter == 5)
            // // {
            // //     var x = 0;
            // //     
            // //     EnvironmentParser intialenvparser = new EnvironmentParser("/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/0onlyLeft.xml");
            // //     //secoundIntialEnv = intialenvparser.ParseEnvironment();
            // //
            // //
            // //     //var sd = EnvironmentComparer.CompareEnvironments(secoundIntialEnv, currentEnvironment);
            // //     
            // //     
            // //     EnvironmentParser news = new EnvironmentParser("/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/currentAtFive.xml");
            // //     news.WriteEnvironment(currentEnvironment);
            // //     
            // //     EnvironmentParser xc = new EnvironmentParser("/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/inital.xml");
            // //     xc.WriteEnvironment(initialEnvironmentState);
            // //     
            // //     
            // //     
            // //     
            // //     
            // //
            // // }
            // //
            // // if (counter <= 5)
            // // {
            // //     EnvironmentParser tryparser = new EnvironmentParser($"/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/{counter}onlyLeft.xml");
            // //     tryparser.WriteEnvironment(currentEnvironment);
            // // }
            //
            //
            // if (counter == 4)
            // {
            //     var x = 0;
            // }           
            if ( currentEnviromentHashValues.Equals(finalStateHashValue))
            {
                
                // Get the list of actions that led to this environment state
                if (instructionStateDictionary.TryGetValue(currentEnviromentHashValues,out  List<string> instructionSet ))
                {
                   results.Add(new object[] { string.Join(", ", instructionSet), "Safe" });
                   return results;
                   Console.WriteLine("####Found instruction set###");
                }
                
                Console.WriteLine("Found final state but could not found final instructions sets###");
                return results;
            }
            
            
            // Retrieve remaining actions for this state
            List<string> remainingActions = new List<string>();
          
                remainingActions = AddEnvironmentAndCheckActions(currentEnviromentHashValues, actionSpace, completedActionsDictionary);
            
           
            
          
            // else
            // {
            //     remainingActions = GetRemaingActions(currentEnvironment, actionSpace, completedActionsDictionary);
            //     
            // }
            
            // else
            // {
            //     if (.(initialEnvironmentState)&& counter !=0 )
            //     {
            //         continue;
            //     }
            //     Console.WriteLine("aDDING NEW STATE IN ACTION MATRIX");
            //     foreach (var action in actionSpace.Actions.ActionList)
            //     {
            //             remainingActions.Add(action.Name); 
            //     }
            //    
            //     completedActionsDictionary.TryAdd(currentEnvironment, remainingActions);
            //      
            //  }

            // if (instructionStateDictionary.Count > 4)
            // {
            //     foreach (var action in instructionStateDictionary)
            //     {
            //         if (action.Key.Equals(currentEnvironment))
            //         {
            //             instructionStateDictionary.Add(currentEnvironment, new List<string>());
            //             continue;
            //             
            //             
            //         }
            //     }
            // }

            // if (!remainingActionsDictionary.TryGetValue(currentEnvironment, out remainingActions))
            // {
            //     remainingActions = GetRemaingActions(currentEnvironment, actionSpace, remainingActionsDictionary);
            //     remainingActionsDictionary[currentEnvironment] = remainingActions;
            // }

            //List<string> actionRemaing=  GetRemaingActions(currentEnvironment, actionSpace, remainingActionsDictionary);

            List<string> actionsToRemove = new List<string>();
            PythonRunner runner = new PythonRunner();

            foreach (string action in new List<string>(remainingActions))
            {
                string filePath = Program.envConfigFile;

                // Run the Python script to get the updated environment statE
                Environment updatedEnvironment =
                    runner.RunPythonScript( filePath, action, out bool safeCondition,out string updatedEnviromentHashValue);
                
                
                EnvironmentParser done = new EnvironmentParser("/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/Task_0/done.xml");
                done.WriteEnvironment(updatedEnvironment,out string current);

                //updatedEnviromentHashValue = current;

                if (current.Equals(finalEnvironmentState))
                {
                    Console.WriteLine("####Found instruction set###");
                }

                if (updatedEnvironment.Equals(finalStateHashValue))
                {
                    Console.WriteLine("####Found final state but could not found final state###");
                }
                
                //bool createdNewKey = instructionStateDictionary.TryAdd(updatedEnviromentHashValue, new List<string>());

                
                //Console.WriteLine($"Created new {createdNewKey}");
                
                bool createdNewActionKey = completedActionsDictionary.TryAdd(updatedEnviromentHashValue,new List<string>());
                
                
                // testing
                var updatedAgent = updatedEnvironment.Agents.AgentList.FirstOrDefault();
                var initialAgent = initialEnvironmentState.Agents.AgentList.FirstOrDefault();
                var currentAgent = currentEnvironment.Agents.AgentList.FirstOrDefault();
                //
                //
                Console.WriteLine($"Initial agent position {initialAgent.Position.Attributes[0].Value.ValueData},{initialAgent.Position.Attributes[1].Value.ValueData} direction {initialAgent.Direction.Attributes[0].Value.ValueData}");
                Console.WriteLine($"current agent position {currentAgent.Position.Attributes[0].Value.ValueData},{currentAgent.Position.Attributes[1].Value.ValueData} direction {currentAgent.Direction.Attributes[0].Value.ValueData}");
                Console.WriteLine(action);
                Console.WriteLine($"updated  agent position {updatedAgent.Position.Attributes[0].Value.ValueData},{updatedAgent.Position.Attributes[1].Value.ValueData} direction {updatedAgent.Direction.Attributes[0].Value.ValueData}");


                // if (updatedEnvironment.Equals(finalEnvironmentState))
                // {
                //     Console.WriteLine("found");
                //     List<string> instructionSet = new List<string>(instructionStateDictionary[currentEnvironment]);
                //     instructionSet.Add(action);
                //     results.Add(new object[] { string.Join(", ", instructionSet), "yes" });
                //     return results;
                //     
                // }


                //
                // if (updatedAgent.Position.Attributes[0].Value.ValueData ==
                //     finalAgentd.Position.Attributes[0].Value.ValueData &&
                //     updatedAgent.Position.Attributes[1].Value.ValueData ==
                //     finalAgent.Position.Attributes[1].Value.ValueData)
                // {
                //     Console.WriteLine("found");
                //     List<string> instructionSet = new List<string>(instructionStateDictionary[currentEnvironment]);
                //     instructionSet.Add(action);
                //     results.Add(new object[] { string.Join(", ", instructionSet), "yes" });
                //     return results;
                // }

                //Console.WriteLine($"Dictyionary size = {instructionStateDictionary.Count}");
                //Console.WriteLine($"Que siz bedore exproling dic size = {environmentQueue.Count}");
                

                List<string> newInstructionSet = new List<string>();

                if (instructionStateDictionary.TryAdd(updatedEnviromentHashValue, new List<string>())&& safeCondition == true)
                {
                    if(instructionStateDictionary.TryGetValue(currentEnviromentHashValues, out List<string> previousInstructionSet ))
                    {
                        newInstructionSet = previousInstructionSet;
                    }
                    
                    
                    newInstructionSet.Add(action);
                    instructionStateDictionary[updatedEnviromentHashValue] =  newInstructionSet;
                    //newInstructionSet.Add(action);
                    Console.WriteLine(newInstructionSet);
                   
                    environmentQueue.Enqueue(updatedEnvironment);
                }
            
               

                 // List<string> instructionSet = instructionStateDictionary[currentEnvironment];
                 // results.Add(new object[] { string.Join(", ", instructionSet), "no" }); 
                 

                 if (safeCondition == false)
                 {
                     List<string> InstructionSet = new List<string>();
                     newInstructionSet.Add(action);
                     instructionStateDictionary[updatedEnviromentHashValue] =  newInstructionSet;
                     results.Add(new object[] { string.Join(", ", newInstructionSet), "Unsafe" }); 
                 }
                 
                 
                // Update the remaining actions dictionary by removing the processed actions
                // if (remainingActionsDictionary.ContainsKey(currentEnvironment))
                // {
                //     remainingActionsDictionary[currentEnvironment].Remove(action);
                // }
            }

            
            counter++;
            
        }

        Logger.LogInfo("Stopping instruction validation.");

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
                Console.WriteLine("Environment already exists in the dictionary. Returning empty list.");
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

   
}