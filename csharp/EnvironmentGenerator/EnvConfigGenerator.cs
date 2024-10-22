using AIprobe.Logging;
using AIprobe.Parsers;
using Environment = AIprobe.Models.Environment;

namespace AIprobe.EnvironmentGenerator
{
    public class EnvConfigGenerator
    {
        /// <summary>
        /// Generate various env based on the initial environment provide by user.
        /// </summary>
        /// <param name="initialEnvironment">initial env object</param>
        /// <returns>list of mutated env object</returns>
        public List<AIprobe.Models.Environment> GenerateEnvConfigs(Environment initialEnvironment, int seed)
        {
            Random random = new Random(seed);
            List<AIprobe.Models.Environment> environments = new List<Environment>();
            
            
            int randomNumberOfEnviroment = random.Next(1, 13);

            Logger.LogInfo($"Environment generation started.");


            environments = hardCodedEnvironments(initialEnvironment);
           
            //0,0
            
            
        
            
            
            
            // for (int i = 0; i < randomNumberOfEnviroment-2; i++)  // Generate 10 random environments
            // {
            //     // Deep copy the initial environment to preserve the original state for each iteration
            //     Environment initialEnvironmentCopy = Program.DeepCopy(initialEnvironment);
            //     List<int> objectIdList = CheckNameTagsMatch(initialEnvironmentCopy);
            //
            //     // Loop through the objects in the environment and mutate based on random number for that environment
            //     foreach (int objectId in objectIdList)
            //     {
            //         // Random number for the action (add/remove object)
            //         int randomNumber = random.Next(0, 2);
            //         //Console.WriteLine($"Random number for object {objectId} in environment {i + 1}: {randomNumber}");
            //
            //         if (randomNumber == 1)
            //         {
            //             // Add a new object
            //             AddNewObject(initialEnvironmentCopy);
            //         }
            //         else
            //         {
            //             // Remove an object
            //             RemoveObjectById(initialEnvironmentCopy, objectId);
            //         }
            //       
            //     }
            //     
            //     
            //
            //     // Add the mutated environment to the list
            //     environments.Add(initialEnvironmentCopy);
            //     Logger.LogInfo($"Environment {i + 1} generation completed.");
            // }
            //
            //
            
            // 
            

            Logger.LogInfo("All environments generated successfully.");
            return environments;
        }



        private List<AIprobe.Models.Environment>  hardCodedEnvironments(AIprobe.Models.Environment environments)
        {
            //0,0
            List<AIprobe.Models.Environment> environmentsList = new List<Environment>();
            
            // Get all XML files from the specified directory
            string[] xmlFiles = Directory.GetFiles(Program.testingHardCoddedEnvs, "*.xml");
    
            if (xmlFiles.Length == 0)
            {
                Logger.LogError("No XML files found in the specified directory.");
                return environmentsList; // Return an empty list if no XML files are found
            }
            
            
            foreach (var filePath in xmlFiles)
            {
                EnvironmentParser initialParser = new EnvironmentParser(filePath);
                AIprobe.Models.Environment initialEnvironment = initialParser.ParseEnvironment();

                // You can now mutate or modify the initialEnvironment as needed
                // For example, you can deep copy it and generate variations

                // Add the initial environment (parsed from XML) to the environments list
                environmentsList.Add(initialEnvironment);
                Logger.LogInfo($"Parsed environment from file: {filePath}");
            }
            
            Logger.LogInfo($"Edge case environment with 0 objects added.");
            
            
            return environmentsList;
            
        }
        
        /// <summary>
        /// Adds a new object to the environment.
        /// </summary>
        /// <param name="environmentConfig">The environment configuration to modify</param>
        /// <summary>
        /// Adds a new object to the environment by finding an existing object with the same name and only changing its Id.
        /// </summary>
        /// <param name="environmentConfig">The environment configuration to modify</param>
        private void AddNewObject(Environment environmentConfig)
        {
            // Find an object with the same name (can be the first match or a random one)
            var existingObject = environmentConfig.Objects.ObjectList
                .OrderBy(_ => Guid.NewGuid()) // Shuffle the list to randomly pick one
                .FirstOrDefault(obj => obj.Name == "ObjectNameYouAreMatching"); // Replace with the actual matching condition

            if (existingObject == null)
            {
                Logger.LogError("No matching object found to copy from.");
                return; // Exit if no matching object is found
            }

            // Create a new object by copying properties from the found object and assigning a new Id
            var newObject = new AIprobe.Models.Object
            {
                Id = environmentConfig.Objects.ObjectList.Max(obj => obj.Id) + 1, // Generate a new Id
                Name = existingObject.Name,  // Keep the same name as the found object
                Position = existingObject.Position,
                ObjectAttributes = existingObject.ObjectAttributes
                
                // Copy other relevant properties as needed
            };

            environmentConfig.Objects.ObjectList.Add(newObject);
            Logger.LogInfo($"Added new object with Id: {newObject.Id}, copied from object with Id: {existingObject.Id}");
        }


        /// <summary>
        /// Removes an object from the environment based on its Id.
        /// </summary>
        /// <param name="environmentConfig">The environment configuration to modify</param>
        /// <param name="objectId">The Id of the object to remove</param>
        private void RemoveObjectById(Environment environmentConfig, int objectId)
        {
            var objectToRemove = environmentConfig.Objects.ObjectList
                .FirstOrDefault(obj => obj.Id == objectId);
            if (objectToRemove != null)
            {
                environmentConfig.Objects.ObjectList.Remove(objectToRemove);
                Logger.LogInfo($"Removed object with Id: {objectId}");
            }
        }


        
        
        /// <summary>
        /// Checks if the name tags of environment properties and object names match.
        /// </summary>
        /// <param name="environmentConfig">The environment configuration object containing agents and objects.</param>
        /// <returns>A list of tuples indicating whether names match and their corresponding names.</returns>
        public List<int> CheckNameTagsMatch(Environment environmentConfig)
        {
            var results = new List<int>();

            // Check names of agents in the environment

            // Check names of objects in the environment
            foreach (var obj in environmentConfig.Objects.ObjectList)
            {
                // Assuming object has a property Name
                string objectName = obj.Name;

                // Compare object names with environment property names
                bool isMatch = environmentConfig.Objects.ObjectList
                    .Any(agent => agent.Name == objectName);

                foreach (var env in environmentConfig.EnvironmentalProperties.Properties)
                {
                    if (env.Name == objectName)
                    {
                        results.Add(obj.Id);
                    }
                    
                }
                
                //bool isInProperties = environmentConfig.EnvironmentalProperties.PropertiesContains(objectName);

               ; // Agent names are null for this case
            }

            Logger.LogInfo("Checked name tags for agents and objects.");
            return results;
        }

    
    }
}

