using AIprobe.Logging;

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
    public List<object[]>  InstructionExists(AIprobe.Models.Environment initialEnvironmentState, AIprobe.Models.Environment finalEnvironmentState,int timeLimitInSeconds)
    {
        List<object[]> results = new List<object[]>();
        
        Logger.LogInfo("Starting instruction validation.");
        
        // Logic here  
        //results.Add(new object[] { instructionSet, isValid ? "yes" : "no" });
        
        Logger.LogInfo("Stopping instruction validation.");
        return results; 
     
    }
    
}