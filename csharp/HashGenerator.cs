using System.Security.Cryptography;
using System.Text;
using Newtonsoft.Json;
using Environment = AIprobe.Models.Environment;

namespace AIprobe;

public class HashGenerator
{


    /// <summary>
    /// Computes the SHA256 hash of the given Environment object.
    /// </summary>
    /// <param name="environment">The Environment object to hash.</param>
    /// <returns>A string representing the SHA256 hash.</returns>
    public static string ComputeEnvironmentHash(Environment environment)
    {
        if (environment == null)
            throw new ArgumentNullException(nameof(environment));

        // Serialize the object to JSON
        string jsonString = JsonConvert.SerializeObject(environment, Formatting.None);

        // Compute the SHA256 hash
        using (SHA256 sha256 = SHA256.Create())
        {
            byte[] hashBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(jsonString));
            return BitConverter.ToString(hashBytes).Replace("-", "").ToLowerInvariant();
        }
    }    
}