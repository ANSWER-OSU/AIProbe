using AIprobe.Logging;

namespace AIprobe.TaskGenerator
{
    public class EnvTaskGenerator
    {
        /// <summary>
        /// Genrate various task based on the env in the given time 
        /// </summary>
        /// <param name="environmentConfig">environment config object</param>
        /// <param name="timeLimitInSeconds">time </param>
        /// <returns></returns>
        public List<AIprobe.Models.Environment> GenerateTasks(AIprobe.Models.Environment environmentConfig , int timeLimitInSeconds)
        {
            List<AIprobe.Models.Environment> tasks = new List<AIprobe.Models.Environment>();
            DateTime startTime = DateTime.Now;

            Logger.LogInfo($"Task generation started with a time limit of {timeLimitInSeconds} seconds.");
            
            int taskCount = 0;
            while ((DateTime.Now - startTime).TotalSeconds < timeLimitInSeconds)
            {
                //logic of creating task
            }
            
            
            Logger.LogInfo($"Task generation completed. {tasks.Count} tasks were generated within {timeLimitInSeconds} seconds.");
            return tasks;
            
        }
    
    }
    
    
}

