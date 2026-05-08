using UnityEngine;

public class SignAnimationController : MonoBehaviour
{
    [SerializeField] private Animator avatarAnimator;

    public void PlayThankYou()
    {
        Debug.Log("THANK_YOU animation requested.");

        if (avatarAnimator == null)
        {
            Debug.LogWarning("Avatar Animator is not assigned.");
            return;
        }

        avatarAnimator.Play("THANK_YOU_TEST", 0, 0f);
    }
}