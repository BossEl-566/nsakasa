using UnityEngine;

public class RotateTestAvatar : MonoBehaviour
{
    [SerializeField] private float rotationSpeed = 35f;

    private void Update()
    {
        transform.Rotate(Vector3.up, rotationSpeed * Time.deltaTime);
    }
}