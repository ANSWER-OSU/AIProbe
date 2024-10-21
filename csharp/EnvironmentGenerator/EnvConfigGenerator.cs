// using AIprobe.Logging;
// using Environment = AIprobe.Models.Environment;
//
// namespace AIprobe.EnvironmentGenerator
// {
//     public class EnvConfigGenerator
//     {
//         /// <summary>
//         /// Generate various env based on the initial environment provide by user.
//         /// </summary>
//         /// <param name="initialEnvironment">initial env object</param>
//         /// <returns>list of mutated env object</returns>
//         public List<AIprobe.Models.Environment> GenerateEnvConfigs(Environment initialEnvironment,int seed)
//         {
//             Random random = new Random(seed);
//             
//             int randomNumber = random.Next(0, 101);
//             Console.WriteLine(randomNumber);
//           
//             List<AIprobe.Models.Environment> environments = new List<Environment>();
//             
//             Logger.LogInfo($"Environment generation started.");
//             
//             Environment initialEnvironmentCopy = Program.DeepCopy(initialEnvironment);
//             List<int> objectIdList = CheckNameTagsMatch(initialEnvironmentCopy);
//
//             foreach (int objectId in objectIdList)
//             {
//                 
//             }
//             
//             
//             
//             
//             
//             
//             
//             
//             
//             // logic to generate different environments based on the initial one
//
//             return environments;
//         }
//         
//         
//         
//         
//         
//         private void MinimumEnviroment
//         
//         
//         /// <summary>
//         /// Checks if the name tags of environment properties and object names match.
//         /// </summary>
//         /// <param name="environmentConfig">The environment configuration object containing agents and objects.</param>
//         /// <returns>A list of tuples indicating whether names match and their corresponding names.</returns>
//         public List<int> CheckNameTagsMatch(Environment environmentConfig)
//         {
//             var results = new List<int>();
//
//             // Check names of agents in the environment
//
//             // Check names of objects in the environment
//             foreach (var obj in environmentConfig.Objects.ObjectList)
//             {
//                 // Assuming object has a property Name
//                 string objectName = obj.Name;
//
//                 // Compare object names with environment property names
//                 bool isMatch = environmentConfig.Objects.ObjectList
//                     .Any(agent => agent.Name == objectName);
//
//                 foreach (var env in environmentConfig.EnvironmentalProperties.Properties)
//                 {
//                     if (env.Name == objectName)
//                     {
//                         results.Add(obj.Id);
//                     }
//                     
//                 }
//                 
//                 //bool isInProperties = environmentConfig.EnvironmentalProperties.PropertiesContains(objectName);
//
//                ; // Agent names are null for this case
//             }
//
//             Logger.LogInfo("Checked name tags for agents and objects.");
//             return results;
//         }
//
//     
//     }
// }
//
