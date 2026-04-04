Suspicion and Noise

If the noise is above the detectable threshold but not the directable threshold:
- Stop, perform scout.
- Increase suspicion score
- If the suspicion score is above a certain threshold, any directional noise prompts alerted state
If the noise is above the directable threshold, suspicion not above threshold:
- Create search path, using search behaviour to the source of the noise. Perform a scout once at the noise 
- Exactly like the search behaviour but for noise source.
Alerted state means that the enemy chases toward the source of the noise, on reaching, if no presence detected, returns to patrol but the suspicion score stays high, so if the player makes another directable noise, then the enemy will go back to chase instantly. 

The suspicion score constantly decays - include dt in update_suspicion, to handle incoming events in the same epoch
enemy will have update suspicion, will be unaware of noise since level is the orchestrator, so level will call update suspicion for each enemy in its own update function. dt will be passed down to the decay function. 
For the player, all actions create noise, with varying levels. I think it is important to include a noise type as well. This can be implemented in the enemy chase, where the enemies create an alarm noise which routes nearby enemies to the player (wishlist)

Attacking makes noise - this should be differentiated from movement noise

It would make sense for enemy suspicion to be more sensitive as it resets from a chase behaviour, so a suspicion multiplier can be implemented which directly affects suspicion accrual. There should be a cap to the suspicion multiplier, therefore a cap to suspicion.

Maybe make noise visible like expanding circles across the map.

suspicion score and multipler is increased through sight of a dead body, so any noise made after that sighting means the enemy will be alerted.

Example flow:

NoiseEvent created
Level calculates percieved intensity for each enemy
If perceived intensity above Detectable threshold but not directable threshold, enemy increases suspicion
If perceived intensity above Directable threshold, enemy starts alerted phase when suspicion high enough. 
Alerted phase is similar to a search, but it is faster, and warrants an increase in both suspicion and suspicion multiplier
If a NoiseEvent happens mid alert which has a higher intensity than the last heard noise, that will override the alerted search target to its position.

New enemy states:

Implicit state - suspicious - when suspicion score > 0
explicit states:
- alerted - prompts search:
    - happens with a directable sound and a high enough suspicion score
- investigative - stops enemy mid-patrol, prompts scout in place, slow turn speed. if no sighting/further sound, continues patrol, suspicion score and multiplier increases.

Existing Functions:
_process_noise()
takes noise, checks all enemies' percieved noise, updates enemy.last_heard


Functions needed:

behavioural controlling should be like other behaviours, where level calls transition_tostate(), and the enemy handles internal logic. Level decides whether noise is detectable/directable, calls different transition_tostate(), this change is reflected in the update function of the enemy. 

therefore transition_investigative() and transition_alert() is necessary
these would trigger specific per-frame update functions investigate() and alert(), which enable behaviour
these functions need to be called in update()

transition_alert would need to change based on a new louder last_heard, so let us see where we can do this:

_process_noise(). changes enemy.last_heard to a NoiseEvent, with a percieved intensity and a position if any.
the enemy needs access to both position to pathfind, and noise_intensity to store and check for a louder one in transition_alert()
therefore transition_alert(self, position, intensity) -> intensity would go to self.last_heard
A condition would exist in level._process_noise(), where if enemy.last_heard < percieved, a new transition_alert() is conducted with the new position and intensity.
transition_investigative() doesn't take any parameters because none of its behaviour is dependent on a position, and level handles when it is called.

transition_investigate(), change state to "investigate", change self.speed to 0, self.turn_speed to lower value -> means resetting of these is necessary in every other state, because it could technically branch to any other state.
transition_alert(), change state to "alert", find path between enemy and source of sound, similar pathfinding to transition_search(), self.speed increases, self.view_distance increases.
investigate() -> , behaviour similar to scout, reduced turn speed
alert() -> follows alert_path to source of directable noise.

in the level loop, to increase suspicion, need to map certain intensities to suspicion via a function. suspicion increases when percieved noise is above a detectable threshold. level function, update_suspicion(self, enemy, intensity): suspicion function takes values above 50, suspicion will increase linearly with intensity of noise. 

check if value above 50, multiply intensity by suspicion conversion constant, add to enemy.suspicion.
suspicion decay, every frame, decay suspicion by  suspicion decay constant * dt












Functions to include:

- dt is a measure of time between frames, informs how often to perform functions.

LEVEL: process_noise(dt)
    # collect all noise events this frame:
    if player is moving:
        create Noise at player's position with intensity proportional to player's speed
    if player is attacking:
        create Noise at player's position with intensity proportional to attack

    # update enemies
    for each enemy:
        for each Noise event:
            distance_sq = square distance between enemy position and noise position
            perceived_intensity = noise_intensity / distance_sq
            store percieved intensity as candidate
        
        target = loudest candidate noise
        
        call update_suspicion(enemy, target_intensity, dt)

        if target_intensity > DIRECTABLE_THRESHOLD:
            if enemy_suspicion >= SUSPICION_THRESHOLD:
                if target_intensity > enemy's last heard noise_intensity:
                    update enemy last heard noise
                    call enemy.alerted()
        
        else if target.intensity > DETECTABLE_THRESHOLD:
            call enemy.investigate()


LEVEL: update_suspicion(enemy, intensity, dt):

    # decay
    enemy.suspicion -= SUSPICION_DECAY_CONSTANT * dt
    clamp this to a minimum zero score

    # accrue suspicion if noise is detectable
    if intensity > DETECTABLE_THRESHOLD:
        gain = (intensity - DETECTABLE_THRESHOLD)
                * SUSPICION_CONVERSION_CONSTANT
                * enemy.suspicion_multiplier
        enemy.suspicion += gain
        clamp to SUSPICION_CAP maximum
    
LEVEL: update_vision_cones(dt):
    FOR EACH enemy:
    IF dead body in vision cone:
      spike enemy.suspicion upward
      increase enemy.suspicion_multiplier
      clamp both to caps

    IF player in vision cone:
      call enemy.chase()

    IF enemy was chasing but lost sight:
      increase enemy.suspicion_multiplier   # post-chase sensitivity
      clamp to SUSPICION_MULTIPLIER_CAP
      call enemy.search()